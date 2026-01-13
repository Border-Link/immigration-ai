"""
Case Eligibility API Views

API endpoints for running eligibility checks and retrieving explanations.
Implements the endpoints from implementation.md Section 4.3.

Features:
- Run eligibility checks for cases (reviewer/admin only)
- Get detailed explanations for eligibility results
- Comprehensive error handling and validation
- Missing documents identification
- Missing requirements formatting
- Citations and reasoning logs
"""
import logging
from rest_framework import status
from typing import List, Optional, Dict, Any
from django.utils import timezone
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_reviewer_or_admin import IsReviewerOrAdmin
from main_system.permissions.case_permission import CasePermission
from immigration_cases.services.case_service import CaseService
from ai_decisions.services.eligibility_check_service import EligibilityCheckService
from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
from ai_decisions.selectors.ai_reasoning_log_selector import AIReasoningLogSelector
from ai_decisions.selectors.ai_citation_selector import AICitationSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.services.rule_engine_service import RuleEngineService
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector

logger = logging.getLogger('django')


class CaseEligibilityCheckAPI(AuthAPI):
    """
    Run eligibility check for a case.
    
    Endpoint: POST /api/v1/cases/{case_id}/eligibility
    Auth: Required (reviewer OR admin/staff only)
    
    Note: Regular users cannot request eligibility checks manually.
    Eligibility checks are automatically triggered by the system when appropriate
    (e.g., when case is submitted, when documents are processed).
    Only reviewers and admins can manually request eligibility checks for review purposes.
    """
    permission_classes = [IsReviewerOrAdmin]
    
    def post(self, request, id):
        """
        Run eligibility check for a case.
        
        Request body (optional):
        {
            "visa_type_ids": ["uuid1", "uuid2"],  // Optional: filter specific visa types
            "enable_ai_reasoning": true  // Optional: enable AI reasoning (default: true)
        }
        """
        # Get case
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Permission check: Only reviewers and admins can request eligibility checks
        # The permission_classes already enforce this, but we verify case access
        user = request.user
        if not self._has_permission(user, case):
            return self.api_response(
                message="You do not have permission to request eligibility checks for this case.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get and validate request parameters
        visa_type_ids = request.data.get('visa_type_ids', [])
        enable_ai_reasoning = request.data.get('enable_ai_reasoning', True)
        
        # Validate visa_type_ids format if provided
        if visa_type_ids:
            if not isinstance(visa_type_ids, list):
                return self.api_response(
                    message="visa_type_ids must be a list of UUIDs.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate each ID is a valid UUID format
            try:
                import uuid
                for vid in visa_type_ids:
                    uuid.UUID(str(vid))  # Validate UUID format
            except (ValueError, TypeError) as e:
                return self.api_response(
                    message=f"Invalid visa_type_id format: {str(e)}",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate enable_ai_reasoning is boolean
        if not isinstance(enable_ai_reasoning, bool):
            return self.api_response(
                message="enable_ai_reasoning must be a boolean.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # If no visa types specified, get all active visa types for jurisdiction
        if not visa_type_ids:
            # Get all active visa types for the case's jurisdiction
            visa_types = VisaTypeSelector.get_by_jurisdiction(case.jurisdiction)
            visa_type_ids = [str(vt.id) for vt in visa_types]
            
            if not visa_type_ids:
                return self.api_response(
                    message=f"No active visa types found for jurisdiction {case.jurisdiction}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Limit number of visa types to prevent abuse
        MAX_VISA_TYPES = 10
        if len(visa_type_ids) > MAX_VISA_TYPES:
            return self.api_response(
                message=f"Too many visa types specified. Maximum {MAX_VISA_TYPES} allowed.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Run eligibility checks for each visa type
        results = []
        all_requires_review = False
        low_confidence_flags = []
        errors = []  # Track errors for individual visa types
        
        for visa_type_id in visa_type_ids:
            try:
                # Validate visa type exists
                visa_type = VisaTypeSelector.get_by_id(visa_type_id)
                if not visa_type:
                    errors.append({
                        'visa_type_id': visa_type_id,
                        'error': 'Visa type not found'
                    })
                    logger.warning(f"Visa type {visa_type_id} not found for eligibility check")
                    continue
                
                # Run eligibility check
                check_result = EligibilityCheckService.run_eligibility_check(
                    case_id=str(case.id),
                    visa_type_id=visa_type_id,
                    enable_ai_reasoning=enable_ai_reasoning
                )
                
                if not check_result:
                    errors.append({
                        'visa_type_id': visa_type_id,
                        'visa_code': visa_type.code,
                        'error': 'Eligibility check returned no result'
                    })
                    logger.warning(f"Eligibility check returned no result for visa type {visa_type_id}")
                    continue
                
                if not check_result.success:
                    error_msg = check_result.error or 'Eligibility check failed'
                    errors.append({
                        'visa_type_id': visa_type_id,
                        'visa_code': visa_type.code,
                        'error': error_msg
                    })
                    logger.warning(f"Eligibility check failed for visa type {visa_type_id}: {error_msg}")
                    continue
                
                # Get rule engine result details
                rule_engine_result = check_result.rule_engine_result
                rule_version = None
                if check_result.eligibility_result_id:
                    eligibility_result = EligibilityResultSelector.get_by_id(check_result.eligibility_result_id)
                    if eligibility_result:
                        rule_version = eligibility_result.rule_version
                
                # Get missing documents for this visa type
                missing_documents = self._get_missing_documents(
                    case_id=str(case.id),
                    rule_version=rule_version
                ) if rule_version else []
                
                # Build result object matching implementation.md format
                result_data = {
                    'visa_code': visa_type.code,
                    'visa_name': visa_type.name,
                    'outcome': check_result.outcome,  # likely, possible, unlikely
                    'confidence': round(check_result.confidence, 2),  # Round to 2 decimal places
                    'rule_version_id': str(rule_version.id) if rule_version else None,
                    'rule_effective_from': rule_version.effective_from.isoformat() if rule_version and rule_version.effective_from else None,
                    'requirements_passed': rule_engine_result.requirements_passed if rule_engine_result else 0,
                    'requirements_total': rule_engine_result.requirements_total if rule_engine_result else 0,
                    'requirements_failed': rule_engine_result.requirements_failed if rule_engine_result else 0,
                    'requirements_with_missing_facts': rule_engine_result.requirements_with_missing_facts if rule_engine_result else 0,
                    'missing_requirements': self._format_missing_requirements(rule_engine_result) if rule_engine_result else [],
                    'missing_documents': missing_documents,
                    'missing_facts': list(set(rule_engine_result.missing_facts)) if rule_engine_result and rule_engine_result.missing_facts else [],
                    'citations': self._get_citations_for_result(check_result.eligibility_result_id) if check_result.eligibility_result_id else [],
                    'reasoning_summary': check_result.reasoning_summary,
                    'warnings': check_result.warnings if hasattr(check_result, 'warnings') else [],
                }
                
                results.append(result_data)
                
                # Track review requirements
                if check_result.requires_human_review:
                    all_requires_review = True
                
                if check_result.confidence < EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD:
                    low_confidence_flags.append({
                        'visa_code': visa_type.code,
                        'visa_name': visa_type.name,
                        'confidence': round(check_result.confidence, 2),
                        'reason': 'low_confidence',
                        'threshold': EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD
                    })
                    
            except Exception as e:
                logger.error(f"Error processing eligibility check for visa type {visa_type_id}: {e}", exc_info=True)
                errors.append({
                    'visa_type_id': visa_type_id,
                    'error': f"Internal error: {str(e)}"
                })
                continue
        
        # Update case status to 'evaluated' if at least one check succeeded
        if results:
            try:
                updated_case, error_msg, http_status = CaseService.update_case(
                    str(case.id),
                    updated_by_id=str(request.user.id) if request.user else None,
                    reason='Eligibility check completed',
                    status='evaluated'
                )
                if not updated_case and error_msg:
                    logger.warning(f"Failed to update case status to 'evaluated': {error_msg}")
            except Exception as e:
                logger.error(f"Error updating case status: {e}", exc_info=True)
                # Continue - don't fail the entire request if status update fails
        
        # Build response matching implementation.md format
        response_data = {
            'case_id': str(case.id),
            'results': results,
            'requires_human_review': all_requires_review,
            'low_confidence_flags': low_confidence_flags,
            'errors': errors if errors else None,  # Include errors if any
            'summary': {
                'total_checked': len(visa_type_ids),
                'successful': len(results),
                'failed': len(errors),
                'requires_review': all_requires_review,
                'low_confidence_count': len(low_confidence_flags)
            },
            'generated_at': timezone.now().isoformat()
        }
        
        # Determine appropriate message
        if errors and not results:
            message = f"Eligibility check completed with errors. {len(errors)} visa type(s) failed."
            status_code = status.HTTP_207_MULTI_STATUS  # Multi-status for partial success
        elif errors:
            message = f"Eligibility check completed. {len(results)} succeeded, {len(errors)} failed."
            status_code = status.HTTP_207_MULTI_STATUS
        else:
            message = "Eligibility check completed successfully."
            status_code = status.HTTP_200_OK
        
        return self.api_response(
            message=message,
            data=response_data,
            status_code=status_code
        )
    
    def _has_permission(self, user, case) -> bool:
        """
        Check if user has permission to request eligibility check for case.
        
        Rules:
        - User is reviewer (role='reviewer' AND is_staff/is_superuser) - can check any case
        - User is admin/staff (is_staff OR is_superuser) - can check any case
        
        Note: Regular users cannot request eligibility checks manually.
        The permission_classes already enforce this at the view level.
        """
        # User is superuser
        if user.is_superuser:
            return True
        
        # User is staff
        if user.is_staff:
            return True
        
        # User is reviewer (must be staff or superuser per IsReviewer permission)
        if user.role == 'reviewer' and (user.is_staff or user.is_superuser):
            return True
        
        # User is admin (role='admin')
        if user.role == 'admin':
            return True
        
        return False
    
    def _format_missing_requirements(self, rule_engine_result) -> List[dict]:
        """
        Format missing/failed requirements from rule engine result.
        
        Only includes requirements that:
        - Failed (passed=False)
        - Have missing facts
        - Have errors
        
        Excludes requirements that passed successfully.
        
        Args:
            rule_engine_result: RuleEngineEvaluationResult instance
            
        Returns:
            List of requirement dictionaries with status information
        """
        if not rule_engine_result or not hasattr(rule_engine_result, 'requirement_details'):
            return []
        
        missing_requirements = []
        
        for req_detail in rule_engine_result.requirement_details:
            passed = req_detail.get('passed', False)
            missing_facts = req_detail.get('missing_facts', [])
            has_error = req_detail.get('error') is not None
            
            # Only include failed, missing facts, or error requirements
            if passed and not missing_facts and not has_error:
                continue  # Skip passed requirements
            
            # Determine status
            if has_error:
                status_value = 'error'
            elif missing_facts:
                status_value = 'missing_fact'
            else:
                status_value = 'failed'
            
            requirement_data = {
                'requirement_code': req_detail.get('requirement_code', 'UNKNOWN'),
                'description': req_detail.get('description', ''),
                'status': status_value,
            }
            
            # Add additional context if available
            if missing_facts:
                requirement_data['missing_facts'] = missing_facts
            
            if has_error:
                requirement_data['error'] = req_detail.get('error')
            
            # Add explanation if available
            if req_detail.get('explanation'):
                requirement_data['explanation'] = req_detail.get('explanation')
            
            missing_requirements.append(requirement_data)
        
        return missing_requirements
    
    def _get_citations_for_result(self, eligibility_result_id: str) -> List[dict]:
        """
        Get citations for an eligibility result.
        
        Retrieves all citations associated with the AI reasoning log
        for the eligibility result.
        
        Args:
            eligibility_result_id: UUID of the eligibility result
            
        Returns:
            List of citation dictionaries with source information
        """
        try:
            eligibility_result = EligibilityResultSelector.get_by_id(eligibility_result_id)
            if not eligibility_result:
                logger.warning(f"Eligibility result {eligibility_result_id} not found for citations")
                return []
            
            # Get the most recent AI reasoning log for this case
            reasoning_logs = AIReasoningLogSelector.get_by_case(eligibility_result.case)
            if not reasoning_logs.exists():
                logger.debug(f"No reasoning logs found for case {eligibility_result.case.id}")
                return []
            
            # Get the latest reasoning log (most recent first)
            latest_log = reasoning_logs.first()
            if not latest_log:
                return []
            
            # Get citations for this reasoning log
            citations = AICitationSelector.get_by_reasoning_log(latest_log)
            
            citation_data = []
            for citation in citations:
                try:
                    doc_version = citation.document_version
                    source_doc = doc_version.source_document if doc_version else None
                    
                    citation_dict = {
                        'source_url': source_doc.source_url if source_doc else None,
                        'excerpt': citation.excerpt,
                        'document_version_id': str(doc_version.id) if doc_version else None,
                    }
                    
                    # Add page number if available in metadata
                    if doc_version and doc_version.metadata:
                        page_number = doc_version.metadata.get('page_number')
                        if page_number is not None:
                            citation_dict['page_number'] = page_number
                    
                    citation_data.append(citation_dict)
                except Exception as e:
                    logger.warning(f"Error processing citation {citation.id}: {e}")
                    continue
            
            return citation_data
            
        except Exception as e:
            logger.error(f"Error getting citations for eligibility result {eligibility_result_id}: {e}", exc_info=True)
            return []
    
    def _get_missing_documents(self, case_id: str, rule_version) -> List[dict]:
        """
        Get missing documents for a case based on visa document requirements.
        
        Compares required documents (from VisaDocumentRequirement) against
        uploaded documents (from CaseDocument) to identify missing ones.
        
        Args:
            case_id: UUID of the case
            rule_version: VisaRuleVersion instance (or None)
            
        Returns:
            List of missing document dictionaries with type and requirement info
        """
        if not rule_version:
            return []
        
        try:
            # Get case object
            case = CaseService.get_by_id(case_id)
            if not case:
                logger.warning(f"Case {case_id} not found for missing documents check")
                return []
            
            # Get document requirements for this rule version
            doc_requirements = VisaDocumentRequirementService.get_by_rule_version(str(rule_version.id))
            if not doc_requirements.exists():
                return []
            
            # Get uploaded documents for this case
            uploaded_docs = CaseDocumentSelector.get_by_case(case)
            uploaded_doc_types = set()
            for doc in uploaded_docs:
                # Only count verified documents
                if doc.status == 'verified' and doc.document_type:
                    uploaded_doc_types.add(str(doc.document_type.id))
            
            missing_documents = []
            for req in doc_requirements:
                # Check if requirement applies (evaluate conditional logic if present)
                applies = True
                if req.conditional_logic:
                    try:
                        # Evaluate conditional logic against case facts
                        case_facts = RuleEngineService.load_case_facts(case_id)
                        import json_logic
                        applies = json_logic.jsonLogic(req.conditional_logic, case_facts)
                        if not isinstance(applies, bool):
                            applies = bool(applies)
                    except Exception as e:
                        logger.warning(f"Error evaluating conditional logic for document requirement {req.id}: {e}")
                        # Default to True if evaluation fails (safer to show requirement)
                        applies = True
                
                if not applies:
                    continue  # Skip requirements that don't apply
                
                # Check if document is uploaded and verified
                doc_type_id = str(req.document_type.id)
                is_uploaded = doc_type_id in uploaded_doc_types
                
                if not is_uploaded:
                    missing_documents.append({
                        'document_type_id': doc_type_id,
                        'document_type_code': req.document_type.code,
                        'document_type_name': req.document_type.name,
                        'mandatory': req.mandatory,
                        'requirement_id': str(req.id),
                    })
            
            return missing_documents
            
        except Exception as e:
            logger.error(f"Error getting missing documents for case {case_id}: {e}", exc_info=True)
            return []


class CaseEligibilityExplanationAPI(AuthAPI):
    """
    Get detailed explanation for an eligibility result.
    
    Endpoint: GET /api/v1/cases/{case_id}/eligibility/{result_id}/explanation
    Auth: Required
    """
    permission_classes = [CasePermission]
    
    def get(self, request, id, result_id):
        """
        Get detailed explanation for an eligibility result.
        
        Returns:
        - Full reasoning
        - AI reasoning log (prompt, response, model)
        - Citations
        - Rule evaluation details
        """
        # Get case
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Permission check
        user = request.user
        if not self._has_permission(user, case):
            return self.api_response(
                message="You do not have permission to access this case.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get eligibility result
        eligibility_result = EligibilityResultSelector.get_by_id(result_id)
        if not eligibility_result:
            return self.api_response(
                message=f"Eligibility result with ID '{result_id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verify result belongs to case
        if str(eligibility_result.case.id) != str(id):
            return self.api_response(
                message="Eligibility result does not belong to this case.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get AI reasoning log (most recent for this case)
        reasoning_logs = AIReasoningLogSelector.get_by_case(case)
        ai_reasoning_log_data = None
        citation_data = []
        
        if reasoning_logs.exists():
            try:
                latest_log = reasoning_logs.first()
                if latest_log:
                    ai_reasoning_log_data = {
                        'prompt': latest_log.prompt,
                        'response': latest_log.response,
                        'model_name': latest_log.model_name,
                        'created_at': latest_log.created_at.isoformat() if latest_log.created_at else None,
                        'tokens_used': getattr(latest_log, 'tokens_used', None),
                        'processing_time_ms': getattr(latest_log, 'processing_time_ms', None),
                    }
                    
                    # Get citations for this reasoning log
                    citations = AICitationSelector.get_by_reasoning_log(latest_log)
                    for citation in citations:
                        try:
                            doc_version = citation.document_version
                            source_doc = doc_version.source_document if doc_version else None
                            
                            citation_dict = {
                                'source_url': source_doc.source_url if source_doc else None,
                                'excerpt': citation.excerpt,
                                'document_version_id': str(doc_version.id) if doc_version else None,
                            }
                            
                            # Add page number if available in metadata
                            if doc_version and doc_version.metadata:
                                page_number = doc_version.metadata.get('page_number')
                                if page_number is not None:
                                    citation_dict['page_number'] = page_number
                            
                            citation_data.append(citation_dict)
                        except Exception as e:
                            logger.warning(f"Error processing citation {citation.id}: {e}")
                            continue
            except Exception as e:
                logger.error(f"Error getting AI reasoning log: {e}", exc_info=True)
                # Continue without reasoning log data
        
        # Get rule evaluation details
        rule_evaluation_details = self._get_rule_evaluation_details(
            eligibility_result,
            case
        )
        
        # Build response matching implementation.md format
        response_data = {
            'result_id': str(eligibility_result.id),
            'full_reasoning': eligibility_result.reasoning_summary or 'No reasoning available.',
            'ai_reasoning_log': ai_reasoning_log_data,
            'citations': citation_data,
            'rule_evaluation_details': rule_evaluation_details
        }
        
        return self.api_response(
            message="Eligibility explanation retrieved successfully.",
            data=response_data,
            status_code=status.HTTP_200_OK
        )
    
    def _has_permission(self, user, case) -> bool:
        """
        Check if user has permission to access case.
        
        Rules:
        - User owns the case (case.user == user)
        - User is reviewer (role='reviewer' AND is_staff/is_superuser)
        - User is superuser
        """
        # User owns case
        if case.user == user:
            return True
        
        # User is superuser
        if user.is_superuser:
            return True
        
        # User is reviewer (must be staff or superuser per IsReviewer permission)
        if user.role == 'reviewer' and (user.is_staff or user.is_superuser):
            return True
        
        return False
    
    def _get_rule_evaluation_details(self, eligibility_result, case) -> List[dict]:
        """
        Get detailed rule evaluation breakdown.
        
        Re-runs rule engine evaluation to get comprehensive breakdown
        of all requirements with their evaluation results.
        
        Args:
            eligibility_result: EligibilityResult instance
            case: Case instance
            
        Returns:
            List of rule evaluation detail dictionaries
        """
        try:
            if not eligibility_result or not eligibility_result.rule_version:
                logger.warning("Eligibility result has no rule version")
                return []
            
            # Load case facts
            case_facts = RuleEngineService.load_case_facts(str(case.id))
            if not case_facts:
                logger.warning(f"Case {case.id} has no facts for rule evaluation")
                return []
            
            rule_version = eligibility_result.rule_version
            
            # Evaluate all requirements
            evaluation_results = RuleEngineService.evaluate_all_requirements(
                rule_version,
                case_facts
            )
            
            if not evaluation_results:
                logger.warning(f"No evaluation results for rule version {rule_version.id}")
                return []
            
            rule_details = []
            for eval_result in evaluation_results:
                requirement = eval_result.get('requirement')
                if not requirement:
                    continue
                
                # Build explanation
                explanation = eval_result.get('explanation', '')
                if not explanation:
                    passed = eval_result.get('passed', False)
                    missing_facts = eval_result.get('missing_facts', [])
                    has_error = eval_result.get('error') is not None
                    
                    if has_error:
                        explanation = f"Requirement evaluation error: {eval_result.get('error')}"
                    elif missing_facts:
                        explanation = f"Requirement cannot be evaluated: missing facts {', '.join(missing_facts)}"
                    else:
                        explanation = f"Requirement {'passed' if passed else 'failed'}"
                
                rule_detail = {
                    'requirement_code': requirement.requirement_code,
                    'requirement_description': requirement.description if hasattr(requirement, 'description') else '',
                    'expression': requirement.condition_expression,
                    'evaluated_value': eval_result.get('passed', False),
                    'explanation': explanation,
                }
                
                # Add additional context
                if eval_result.get('missing_facts'):
                    rule_detail['missing_facts'] = eval_result.get('missing_facts')
                
                if eval_result.get('error'):
                    rule_detail['error'] = eval_result.get('error')
                
                # Add evaluated expression result if available
                if 'evaluated_expression' in eval_result:
                    rule_detail['evaluated_expression'] = eval_result.get('evaluated_expression')
                
                rule_details.append(rule_detail)
            
            return rule_details
            
        except Exception as e:
            logger.error(f"Error getting rule evaluation details: {e}", exc_info=True)
            return []
