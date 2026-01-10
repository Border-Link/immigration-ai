"""
Case Eligibility API Views

API endpoints for running eligibility checks and retrieving explanations.
Implements the endpoints from implementation.md Section 4.3.
"""
import logging
from rest_framework import status
from typing import List, Optional
from django.utils import timezone
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_service import CaseService
from immigration_cases.selectors.case_selector import CaseSelector
from ai_decisions.services.eligibility_check_service import EligibilityCheckService
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
from ai_decisions.selectors.ai_reasoning_log_selector import AIReasoningLogSelector
from ai_decisions.selectors.ai_citation_selector import AICitationSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.selectors.visa_requirement_selector import VisaRequirementSelector
from rules_knowledge.services.rule_engine_service import RuleEngineService
from users_access.selectors.user_selector import UserSelector

logger = logging.getLogger('django')


class CaseEligibilityCheckAPI(AuthAPI):
    """
    Run eligibility check for a case.
    
    Endpoint: POST /api/v1/cases/{case_id}/eligibility
    Auth: Required (user: own case, reviewer: any case, superuser: any case)
    """
    
    def post(self, request, id):
        """
        Run eligibility check for a case.
        
        Request body (optional):
        {
            "visa_type_ids": ["uuid1", "uuid2"],  // Optional: filter specific visa types
            "enable_ai_reasoning": true  // Optional: enable AI reasoning (default: true)
        }
        """
        try:
            # Get case
            case = CaseSelector.get_by_id(id)
            if not case:
                return self.api_response(
                    message=f"Case with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Permission check: user owns case OR is reviewer OR is superuser
            user = request.user
            if not self._has_permission(user, case):
                return self.api_response(
                    message="You do not have permission to access this case.",
                    data=None,
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            # Get request parameters
            visa_type_ids = request.data.get('visa_type_ids', [])
            enable_ai_reasoning = request.data.get('enable_ai_reasoning', True)
            
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
            
            # Run eligibility checks for each visa type
            results = []
            all_requires_review = False
            low_confidence_flags = []
            
            for visa_type_id in visa_type_ids:
                # Run eligibility check
                check_result = EligibilityCheckService.run_eligibility_check(
                    case_id=str(case.id),
                    visa_type_id=visa_type_id,
                    enable_ai_reasoning=enable_ai_reasoning
                )
                
                if not check_result.success:
                    logger.warning(
                        f"Eligibility check failed for case {id}, visa type {visa_type_id}: {check_result.error}"
                    )
                    continue
                
                # Get visa type details
                visa_type = VisaTypeSelector.get_by_id(visa_type_id)
                if not visa_type:
                    continue
                
                # Get rule engine result details
                rule_engine_result = check_result.rule_engine_result
                rule_version = None
                if check_result.eligibility_result_id:
                    eligibility_result = EligibilityResultSelector.get_by_id(check_result.eligibility_result_id)
                    if eligibility_result:
                        rule_version = eligibility_result.rule_version
                
                # Build result object matching implementation.md format
                result_data = {
                    'visa_code': visa_type.code,
                    'visa_name': visa_type.name,
                    'outcome': check_result.outcome,  # likely, possible, unlikely
                    'confidence': check_result.confidence,
                    'rule_version_id': str(rule_version.id) if rule_version else None,
                    'rule_effective_from': rule_version.effective_from.isoformat() if rule_version and rule_version.effective_from else None,
                    'requirements_passed': rule_engine_result.requirements_passed if rule_engine_result else 0,
                    'requirements_total': rule_engine_result.requirements_total if rule_engine_result else 0,
                    'missing_requirements': self._format_missing_requirements(rule_engine_result) if rule_engine_result else [],
                    'missing_documents': [],  # TODO: Implement document requirement checking
                    'citations': self._get_citations_for_result(check_result.eligibility_result_id) if check_result.eligibility_result_id else [],
                    'reasoning_summary': check_result.reasoning_summary,
                }
                
                results.append(result_data)
                
                # Track review requirements
                if check_result.requires_human_review:
                    all_requires_review = True
                
                if check_result.confidence < EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD:
                    low_confidence_flags.append({
                        'visa_code': visa_type.code,
                        'reason': 'low_confidence'
                    })
            
            # Update case status to 'evaluated' if at least one check succeeded
            if results:
                CaseService.update_case(str(case.id), status='evaluated')
            
            # Build response matching implementation.md format
            response_data = {
                'case_id': str(case.id),
                'results': results,
                'requires_human_review': all_requires_review,
                'low_confidence_flags': low_confidence_flags,
                'generated_at': timezone.now().isoformat()
            }
            
            return self.api_response(
                message="Eligibility check completed successfully.",
                data=response_data,
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error running eligibility check for case {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error running eligibility check.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    
    def _format_missing_requirements(self, rule_engine_result) -> List[dict]:
        """Format missing requirements from rule engine result."""
        missing_requirements = []
        
        for req_detail in rule_engine_result.requirement_details:
            status_value = 'passed' if req_detail.get('passed') else 'failed'
            if req_detail.get('missing_facts'):
                status_value = 'missing_fact'
            
            missing_requirements.append({
                'requirement_code': req_detail.get('requirement_code', 'UNKNOWN'),
                'description': req_detail.get('description', ''),
                'status': status_value
            })
        
        return missing_requirements
    
    def _get_citations_for_result(self, eligibility_result_id: str) -> List[dict]:
        """Get citations for an eligibility result."""
        try:
            eligibility_result = EligibilityResultSelector.get_by_id(eligibility_result_id)
            if not eligibility_result:
                return []
            
            # Get the most recent AI reasoning log for this case
            reasoning_logs = AIReasoningLogSelector.get_by_case(eligibility_result.case)
            if not reasoning_logs.exists():
                return []
            
            # Get the latest reasoning log
            latest_log = reasoning_logs.first()
            
            # Get citations for this reasoning log
            citations = AICitationSelector.get_by_reasoning_log(latest_log)
            
            citation_data = []
            for citation in citations:
                citation_data.append({
                    'source_url': citation.document_version.source_document.source_url,
                    'excerpt': citation.excerpt,
                    'document_version_id': str(citation.document_version.id)
                })
            
            return citation_data
            
        except Exception as e:
            logger.error(f"Error getting citations for result {eligibility_result_id}: {e}")
            return []


class CaseEligibilityExplanationAPI(AuthAPI):
    """
    Get detailed explanation for an eligibility result.
    
    Endpoint: GET /api/v1/cases/{case_id}/eligibility/{result_id}/explanation
    Auth: Required
    """
    
    def get(self, request, id, result_id):
        """
        Get detailed explanation for an eligibility result.
        
        Returns:
        - Full reasoning
        - AI reasoning log (prompt, response, model)
        - Citations
        - Rule evaluation details
        """
        try:
            # Get case
            case = CaseSelector.get_by_id(id)
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
            if reasoning_logs.exists():
                latest_log = reasoning_logs.first()
                ai_reasoning_log_data = {
                    'prompt': latest_log.prompt,
                    'response': latest_log.response,
                    'model_name': latest_log.model_name,
                    'created_at': latest_log.created_at.isoformat()
                }
                
                # Get citations for this reasoning log
                citations = AICitationSelector.get_by_reasoning_log(latest_log)
                citation_data = []
                for citation in citations:
                    citation_data.append({
                        'source_url': citation.document_version.source_document.source_url,
                        'excerpt': citation.excerpt,
                        'document_version_id': str(citation.document_version.id),
                        'page_number': citation.document_version.metadata.get('page_number') if citation.document_version.metadata else None
                    })
            else:
                citation_data = []
            
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
            
        except Exception as e:
            logger.error(f"Error getting eligibility explanation for case {id}, result {result_id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving eligibility explanation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        """Get detailed rule evaluation breakdown."""
        try:
            # Re-run rule engine evaluation to get detailed breakdown
            case_facts = RuleEngineService.load_case_facts(str(case.id))
            rule_version = eligibility_result.rule_version
            
            # Evaluate all requirements
            evaluation_results = RuleEngineService.evaluate_all_requirements(
                rule_version,
                case_facts
            )
            
            rule_details = []
            for eval_result in evaluation_results:
                requirement = eval_result.get('requirement')
                if not requirement:
                    continue
                
                # Build explanation
                explanation = eval_result.get('explanation', '')
                if not explanation:
                    passed = eval_result.get('passed', False)
                    explanation = f"Requirement {'passed' if passed else 'failed'}"
                
                rule_details.append({
                    'requirement_code': requirement.requirement_code,
                    'expression': requirement.condition_expression,
                    'evaluated_value': eval_result.get('passed', False),
                    'explanation': explanation
                })
            
            return rule_details
            
        except Exception as e:
            logger.error(f"Error getting rule evaluation details: {e}", exc_info=True)
            return []
