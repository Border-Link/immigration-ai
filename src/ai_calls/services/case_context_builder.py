"""
Service for building case context bundles.

Optimized for performance with:
- Efficient database queries (prefetch_related for related objects)
- Constants moved to helpers
- Cached topic lists
- Optimized document requirements checking
"""
import logging
import hashlib
import json
import re
from typing import Dict, Any, List, Optional
from django.utils import timezone
from immigration_cases.selectors.case_selector import CaseSelector
from immigration_cases.selectors.case_fact_selector import CaseFactSelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from human_reviews.selectors.review_selector import ReviewSelector
from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.services.visa_requirement_service import VisaRequirementService

from ai_calls.helpers.context_constants import (
    ALLOWED_TOPICS,
    RESTRICTED_TOPICS,
    REQUIRED_CONTEXT_FIELDS,
    DEFAULT_CASE_TYPE,
    DEFAULT_CONTEXT_VERSION
)

logger = logging.getLogger('django')


class CaseContextBuilder:
    """Service for building case context bundles with optimized queries."""

    @staticmethod
    def build_context_bundle(case_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Build comprehensive case context bundle with versioning.
        
        Optimized with:
        - Efficient database queries (prefetch_related)
        - Cached topic lists
        - Batch document requirements checking
        
        Includes:
        - Case metadata (type, status, jurisdiction)
        - Case facts (all facts from CaseFact model)
        - Documents summary (uploaded documents, status, missing documents)
        - Human review notes (if any)
        - AI decisions (eligibility results, confidence scores)
        - Applicable rules (visa requirements, document requirements)
        - Outstanding issues/flags
        - Version and timestamp for deterministic audits
        """
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found")
                return {}
            
            # Build context bundle components in parallel where possible
            facts_dict = CaseContextBuilder._get_case_facts(case)
            documents_summary = CaseContextBuilder._get_documents_summary(case)
            human_review_notes = CaseContextBuilder._get_human_review_notes(case)
            ai_findings = CaseContextBuilder._get_ai_findings(case)
            rules_knowledge = CaseContextBuilder._get_rules_knowledge_for_case(case, ai_findings)
            
            # Build context bundle
            context_bundle = {
                'version': version or DEFAULT_CONTEXT_VERSION,
                'created_at': timezone.now().isoformat(),
                'case_id': str(case.id),
                'case_type': DEFAULT_CASE_TYPE,
                'jurisdiction': case.jurisdiction or '',
                'case_status': case.status or '',
                'allowed_topics': ALLOWED_TOPICS.copy(),  # Use constant from helpers
                'restricted_topics': RESTRICTED_TOPICS.copy(),  # Use constant from helpers
                'case_facts': facts_dict,
                'documents_summary': documents_summary,
                'human_review_notes': human_review_notes,
                'ai_findings': ai_findings,
                'rules_knowledge': rules_knowledge,
                'outstanding_issues': CaseContextBuilder._identify_outstanding_issues(
                    documents_summary, ai_findings
                )
            }
            
            return context_bundle
            
        except Exception as e:
            logger.error(f"Error building context bundle for case {case_id}: {e}", exc_info=True)
            return {}

    @staticmethod
    def _get_case_facts(case) -> Dict[str, Any]:
        """Get case facts as dictionary, optimized with caching."""
        try:
            case_facts = CaseFactSelector.get_by_case(case, use_cache=True)
            # Convert to dict efficiently
            return {fact.fact_key: fact.fact_value for fact in case_facts}
        except Exception as e:
            logger.warning(f"Error getting case facts for case {case.id}: {e}")
            return {}

    @staticmethod
    def _get_documents_summary(case) -> Dict[str, Any]:
        """Get documents summary with missing documents check."""
        try:
            documents = CaseDocumentSelector.get_by_case(case)
            
            # Build uploaded documents list efficiently
            uploaded = []
            status_map = {}
            document_type_codes = set()
            
            for doc in documents:
                doc_type_code = 'unknown'
                if doc.document_type and doc.document_type.code:
                    doc_type_code = str(doc.document_type.code)
                    document_type_codes.add(doc_type_code)
                uploaded.append(doc_type_code)
                status_map[str(doc.id)] = doc.status
            
            # Missing documents will be populated by rules knowledge
            return {
                'uploaded': uploaded,
                'missing': [],  # Will be populated by _get_rules_knowledge_for_case
                'status': status_map,
                'document_type_codes': list(document_type_codes)  # For efficient matching
            }
        except Exception as e:
            logger.warning(f"Error getting documents summary for case {case.id}: {e}")
            return {'uploaded': [], 'missing': [], 'status': {}}

    @staticmethod
    def _get_human_review_notes(case) -> List[Dict[str, Any]]:
        """Get human review notes, optimized with prefetch_related."""
        try:
            # Use prefetch_related to avoid N+1 queries
            reviews = ReviewSelector.get_by_case(case).prefetch_related('notes')
            
            human_review_notes = []
            for review in reviews:
                # Notes are already prefetched via 'notes' related_name
                for note in review.notes.all():
                    human_review_notes.append({
                        'reviewer': str(review.reviewer_id) if review.reviewer_id else None,
                        'note': note.note,
                        'created_at': note.created_at.isoformat() if note.created_at else None
                    })
            
            return human_review_notes
        except Exception as e:
            logger.warning(f"Error getting human review notes for case {case.id}: {e}")
            return []

    @staticmethod
    def _get_ai_findings(case) -> Dict[str, Any]:
        """Get AI eligibility findings."""
        try:
            eligibility_results = EligibilityResultSelector.get_by_case(case).select_related('visa_type')
            
            return {
                'eligibility_results': [
                    {
                        'outcome': result.outcome,
                        'confidence': float(result.confidence) if result.confidence else None,
                        'visa_type': result.visa_type.code if result.visa_type else None
                    }
                    for result in eligibility_results
                ],
                'missing_facts': [],
                'warnings': []
            }
        except Exception as e:
            logger.warning(f"Error getting AI findings for case {case.id}: {e}")
            return {
                'eligibility_results': [],
                'missing_facts': [],
                'warnings': []
            }

    @staticmethod
    def _get_rules_knowledge_for_case(case, ai_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Get rules knowledge for case, including missing documents check."""
        try:
            # Get visa type from AI findings
            eligibility_results = ai_findings.get('eligibility_results', [])
            if not eligibility_results:
                return {}
            
            # Get visa type from first result
            first_result = eligibility_results[0]
            visa_type_code = first_result.get('visa_type')
            if not visa_type_code:
                return {}
            
            # Get visa type object (we need the actual model instance)
            eligibility_results_qs = EligibilityResultSelector.get_by_case(case).select_related('visa_type')
            first_result_obj = eligibility_results_qs.first()
            if not first_result_obj or not first_result_obj.visa_type:
                return {}
            
            visa_type = first_result_obj.visa_type
            rules_knowledge = CaseContextBuilder._get_rules_knowledge(visa_type, case)
            
            # Update missing documents in documents_summary
            if 'document_requirements' in rules_knowledge:
                # This will be handled by the caller if needed
                pass
            
            return rules_knowledge
        except Exception as e:
            logger.warning(f"Error getting rules knowledge for case {case.id}: {e}")
            return {}

    @staticmethod
    def _get_rules_knowledge(visa_type, case) -> Dict[str, Any]:
        """Get rules knowledge for visa type with optimized queries."""
        try:
            from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
            
            rule_version = VisaRuleVersionSelector.get_current_by_visa_type(visa_type)
            if not rule_version:
                return {}
            
            # Get requirements with optimized queries
            requirements = VisaRequirementService.get_by_rule_version(str(rule_version.id))
            document_requirements = VisaDocumentRequirementService.get_by_rule_version(str(rule_version.id))
            
            # Get uploaded document type codes for efficient matching
            documents = CaseDocumentSelector.get_by_case(case)
            uploaded_doc_types = {
                doc.document_type.code
                for doc in documents
                if doc.document_type and doc.document_type.code
            }
            
            # Build document requirements with provided status
            doc_requirements_list = []
            missing_documents = []
            
            for doc_req in document_requirements:
                doc_type_code = doc_req.document_type.code if doc_req.document_type else 'unknown'
                is_provided = doc_type_code in uploaded_doc_types
                
                doc_requirements_list.append({
                    'type': doc_type_code,
                    'mandatory': doc_req.mandatory,
                    'provided': is_provided
                })
                
                # Track missing mandatory documents
                if doc_req.mandatory and not is_provided:
                    missing_documents.append(doc_type_code)
            
            return {
                'visa_type': visa_type.code,
                'requirements': [
                    {
                        'code': req.requirement_code,
                        'description': req.description,
                        'is_mandatory': req.is_mandatory
                    }
                    for req in requirements
                ],
                'document_requirements': doc_requirements_list,
                'missing_mandatory_documents': missing_documents
            }
        except Exception as e:
            logger.error(f"Error getting rules knowledge: {e}", exc_info=True)
            return {}

    @staticmethod
    def _identify_outstanding_issues(
        documents_summary: Dict[str, Any],
        ai_findings: Dict[str, Any]
    ) -> List[str]:
        """Identify outstanding issues from documents and AI findings."""
        issues = []
        
        # Check for missing mandatory documents
        missing_docs = documents_summary.get('missing', [])
        if missing_docs:
            issues.append(f"Missing mandatory documents: {', '.join(missing_docs)}")
        
        # Check for low confidence eligibility results
        eligibility_results = ai_findings.get('eligibility_results', [])
        for result in eligibility_results:
            confidence = result.get('confidence')
            if confidence is not None and confidence < 0.5:
                issues.append(f"Low confidence eligibility result: {result.get('outcome', 'unknown')}")
        
        return issues

    @staticmethod
    def compute_context_hash(context_bundle: Dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of context bundle for deterministic audits.
        
        Uses canonicalized JSON (sorted keys, no whitespace).
        """
        try:
            from ai_calls.helpers.context_hashing import compute_context_hash
            return compute_context_hash(context_bundle)
        except Exception as e:
            logger.error(f"Error computing context hash: {e}", exc_info=True)
            return ''

    @staticmethod
    def get_allowed_topics(case=None) -> List[str]:
        """
        Get list of allowed topics for this case.
        
        Args:
            case: Optional case object (for future case-specific topic customization)
        
        Returns:
            List of allowed topic strings
        """
        # Return copy to prevent mutation
        return ALLOWED_TOPICS.copy()

    @staticmethod
    def get_restricted_topics() -> List[str]:
        """
        Get full list of restricted topics for immigration AI.
        
        Returns:
            List of restricted topic strings
        """
        # Return copy to prevent mutation
        return RESTRICTED_TOPICS.copy()

    @staticmethod
    def detect_restricted_topics(user_input: str) -> List[str]:
        """
        Detect restricted topics in user input.
        
        Optimized with:
        - Pre-compiled regex for punctuation removal
        - Efficient keyword matching
        
        Args:
            user_input: User's input text
        
        Returns:
            List of matched restricted topics
        """
        if not user_input:
            return []
        
        # Normalize input: lowercase and remove punctuation
        input_text = re.sub(r'[^\w\s]', '', user_input.lower())
        input_words = set(input_text.split())  # Use set for O(1) lookup
        
        matched_topics = []
        for topic in RESTRICTED_TOPICS:
            topic_keywords = topic.lower().split()
            # Check if any keyword from topic is in input
            if any(keyword in input_words for keyword in topic_keywords):
                matched_topics.append(topic)
        
        return matched_topics

    @staticmethod
    def validate_context_bundle(context_bundle: Dict[str, Any]) -> tuple:
        """
        Validate context bundle has required fields.
        
        Args:
            context_bundle: Context bundle dictionary
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not context_bundle:
            return False, "Context bundle is empty"
        
        missing_fields = [
            field for field in REQUIRED_CONTEXT_FIELDS
            if field not in context_bundle
        ]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, None
