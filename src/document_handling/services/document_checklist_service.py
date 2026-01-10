"""
Service for generating document checklists based on visa requirements.
"""
import logging
from typing import List, Dict, Any, Optional
from immigration_cases.selectors.case_selector import CaseSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.visa_document_requirement_selector import VisaDocumentRequirementSelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from rules_knowledge.services.rule_engine_service import RuleEngineService

logger = logging.getLogger('django')


class DocumentChecklistService:
    """Service for generating document checklists."""

    @staticmethod
    def generate_checklist(case_id: str) -> Dict[str, Any]:
        """
        Generate a document checklist for a case based on visa requirements.
        
        Args:
            case_id: UUID of the case
            
        Returns:
            Dict with checklist information:
            - case_id: Case ID
            - visa_type: Visa type information
            - rule_version: Rule version information
            - requirements: List of required documents with status
            - summary: Summary statistics
        """
        try:
            # Get case
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found")
                return {
                    'error': 'Case not found',
                    'case_id': case_id
                }
            
            # Get visa type
            if not case.visa_type:
                logger.warning(f"Case {case_id} has no visa type")
                return {
                    'error': 'Case has no visa type',
                    'case_id': case_id,
                    'requirements': [],
                    'summary': {
                        'total_required': 0,
                        'uploaded': 0,
                        'missing': 0,
                        'pending': 0
                    }
                }
            
            # Get current rule version
            rule_version = VisaRuleVersionSelector.get_current_by_visa_type(case.visa_type)
            if not rule_version:
                logger.warning(f"No active rule version found for visa type {case.visa_type.id}")
                return {
                    'error': 'No active rule version found',
                    'case_id': case_id,
                    'visa_type': {
                        'id': str(case.visa_type.id),
                        'name': case.visa_type.name
                    },
                    'requirements': [],
                    'summary': {
                        'total_required': 0,
                        'uploaded': 0,
                        'missing': 0,
                        'pending': 0
                    }
                }
            
            # Get document requirements
            requirements = VisaDocumentRequirementSelector.get_by_rule_version(rule_version)
            
            # Get uploaded documents for this case
            uploaded_documents = CaseDocumentSelector.get_by_filters(case_id=case_id)
            uploaded_document_types = {
                str(doc.document_type.id): doc
                for doc in uploaded_documents
                if doc.document_type
            }
            
            # Load case facts for conditional logic evaluation
            case_facts = {}
            try:
                case_facts = RuleEngineService.load_case_facts(case)
            except Exception as e:
                logger.warning(f"Error loading case facts: {e}")
            
            # Build checklist
            checklist_items = []
            mandatory_count = 0
            uploaded_count = 0
            missing_count = 0
            pending_count = 0
            
            for requirement in requirements:
                document_type = requirement.document_type
                document_type_id = str(document_type.id)
                
                # Check if document is uploaded
                uploaded_doc = uploaded_document_types.get(document_type_id)
                
                # Check conditional logic
                conditional_applies = True
                conditional_details = {}
                if requirement.conditional_logic:
                    try:
                        conditional_result = RuleEngineService.evaluate_expression(
                            requirement.conditional_logic,
                            case_facts
                        )
                        
                        # evaluate_expression always returns a dict with 'passed', 'result', 'error', 'missing_facts'
                        conditional_applies = conditional_result.get('passed', False)
                        conditional_details = conditional_result
                        
                        # If there's an error or missing facts, log it but default to applies
                        if conditional_result.get('error') or conditional_result.get('missing_facts'):
                            logger.warning(
                                f"Conditional logic evaluation had issues: "
                                f"error={conditional_result.get('error')}, "
                                f"missing_facts={conditional_result.get('missing_facts')}"
                            )
                            # Default to applies if evaluation has issues
                            conditional_applies = True
                    except Exception as e:
                        logger.warning(f"Error evaluating conditional logic: {e}")
                        conditional_applies = True  # Default to applies if evaluation fails
                        conditional_details = {'error': str(e), 'default': True}
                
                # Skip if conditional logic doesn't apply
                if not conditional_applies:
                    continue
                
                # Determine status
                if uploaded_doc:
                    if uploaded_doc.status == 'verified':
                        status = 'uploaded'
                        uploaded_count += 1
                    elif uploaded_doc.status == 'rejected':
                        status = 'rejected'
                        missing_count += 1
                    elif uploaded_doc.status == 'needs_attention':
                        status = 'needs_attention'
                        pending_count += 1
                    else:
                        status = 'processing'
                        pending_count += 1
                else:
                    status = 'missing'
                    missing_count += 1
                
                if requirement.mandatory:
                    mandatory_count += 1
                
                checklist_items.append({
                    'requirement_id': str(requirement.id),
                    'document_type': {
                        'id': document_type_id,
                        'name': document_type.name,
                        'code': document_type.code
                    },
                    'mandatory': requirement.mandatory,
                    'status': status,
                    'uploaded_document': {
                        'id': str(uploaded_doc.id),
                        'file_name': uploaded_doc.file_name,
                        'status': uploaded_doc.status,
                        'uploaded_at': uploaded_doc.uploaded_at.isoformat() if uploaded_doc.uploaded_at else None
                    } if uploaded_doc else None,
                    'conditional_logic': requirement.conditional_logic,
                    'conditional_applies': conditional_applies,
                    'conditional_details': conditional_details
                })
            
            # Sort: mandatory first, then by status (missing first)
            checklist_items.sort(key=lambda x: (
                not x['mandatory'],  # Mandatory first
                x['status'] == 'missing',  # Missing first
                x['status'] == 'needs_attention',
                x['status'] == 'processing',
                x['status'] == 'rejected',
                x['status'] == 'uploaded'
            ))
            
            summary = {
                'total_required': len(checklist_items),
                'mandatory': mandatory_count,
                'uploaded': uploaded_count,
                'missing': missing_count,
                'pending': pending_count,
                'needs_attention': sum(1 for item in checklist_items if item['status'] == 'needs_attention'),
                'processing': sum(1 for item in checklist_items if item['status'] == 'processing'),
                'rejected': sum(1 for item in checklist_items if item['status'] == 'rejected')
            }
            
            logger.info(
                f"Generated checklist for case {case_id}: "
                f"total={summary['total_required']}, uploaded={summary['uploaded']}, "
                f"missing={summary['missing']}, pending={summary['pending']}"
            )
            
            return {
                'case_id': case_id,
                'visa_type': {
                    'id': str(case.visa_type.id),
                    'name': case.visa_type.name
                },
                'rule_version': {
                    'id': str(rule_version.id),
                    'version': rule_version.version,
                    'effective_from': rule_version.effective_from.isoformat() if rule_version.effective_from else None
                },
                'requirements': checklist_items,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error generating checklist: {e}", exc_info=True)
            return {
                'error': str(e),
                'case_id': case_id
            }
