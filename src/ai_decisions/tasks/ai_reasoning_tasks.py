"""
AI Reasoning Tasks

Celery tasks for running eligibility checks asynchronously.
"""
from celery import shared_task
import logging
from typing import Dict, Any, Optional, List
from main_system.tasks_base import BaseTaskWithMeta
from ai_decisions.services.eligibility_check_service import EligibilityCheckService
from immigration_cases.selectors.case_selector import CaseSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def run_eligibility_check_task(
    self,
    case_id: str,
    visa_type_id: Optional[str] = None,
    enable_ai_reasoning: bool = True
) -> Dict[str, Any]:
    """
    Celery task to run eligibility check for a case.
    
    This orchestrates the complete eligibility check flow:
    1. Rule engine evaluation
    2. AI reasoning (RAG)
    3. Outcome combination
    4. Result storage
    5. Auto-escalation if needed
    
    Args:
        case_id: UUID of the case
        visa_type_id: Optional visa type ID to check (if None, checks all active visa types)
        enable_ai_reasoning: Whether to run AI reasoning (default: True)
        
    Returns:
        Dict with eligibility check results
    """
    try:
        logger.info(
            f"Starting eligibility check task for case: {case_id}, "
            f"visa_type: {visa_type_id}, ai_reasoning: {enable_ai_reasoning}"
        )
        
        case = CaseSelector.get_by_id(case_id)
        if not case:
            logger.error(f"Case {case_id} not found")
            return {'success': False, 'error': 'Case not found'}
        
        # If visa_type_id provided, check only that visa type
        if visa_type_id:
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            if not visa_type:
                logger.error(f"Visa type {visa_type_id} not found")
                return {'success': False, 'error': 'Visa type not found'}
            
            # Run complete eligibility check
            check_result = EligibilityCheckService.run_eligibility_check(
                case_id=case_id,
                visa_type_id=visa_type_id,
                enable_ai_reasoning=enable_ai_reasoning
            )
            
            return check_result.to_dict()
        else:
            # Check all active visa types for the case's jurisdiction
            # Get all active visa types for the jurisdiction
            jurisdiction = case.jurisdiction if hasattr(case, 'jurisdiction') else None
            if not jurisdiction:
                logger.warning(f"Case {case_id} has no jurisdiction - cannot check all visa types")
                return {
                    'success': False,
                    'error': 'Case has no jurisdiction specified'
                }
            
            # Get all active visa types for this jurisdiction
            # Note: This requires a selector method to get visa types by jurisdiction
            # For now, we'll log and return a message
            logger.info(f"Checking all visa types for case {case_id}, jurisdiction: {jurisdiction}")
            
            # TODO: Implement multi-visa-type checking
            # For now, return a message indicating this feature needs implementation
            return {
                'success': False,
                'error': 'Multi-visa-type checking not yet implemented. Please specify visa_type_id.',
                'message': 'To check all visa types, implement VisaTypeSelector.get_by_jurisdiction()'
            }
        
    except Exception as e:
        logger.error(f"Error running eligibility check task for case {case_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)

