"""
AI Reasoning Tasks

Celery tasks for running eligibility checks asynchronously.

Features:
- Single visa type eligibility checks
- Multi-visa-type eligibility checks (all active visa types for jurisdiction)
- Comprehensive error handling and retry logic
- Task result tracking and metrics
- Edge case handling
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from celery import shared_task
from celery.exceptions import Retry, MaxRetriesExceeded
from django.utils import timezone
from main_system.utils.tasks_base import BaseTaskWithMeta
from ai_decisions.services.eligibility_check_service import EligibilityCheckService, EligibilityCheckResult
from ai_decisions.helpers.metrics import (
    track_eligibility_check,
    track_auto_escalation,
    track_eligibility_conflict
)
from immigration_cases.selectors.case_selector import CaseSelector
from immigration_cases.services.case_service import CaseService
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta, max_retries=3, default_retry_delay=60)
def run_eligibility_check_task(
    self,
    case_id: str,
    visa_type_id: Optional[str] = None,
    enable_ai_reasoning: bool = True,
    evaluation_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Celery task to run eligibility check for a case.
    
    This orchestrates the complete eligibility check flow:
    1. Rule engine evaluation
    2. AI reasoning (RAG)
    3. Outcome combination
    4. Result storage
    5. Auto-escalation if needed
    
    Supports both single visa type and multi-visa-type checking.
    
    Args:
        case_id: UUID of the case (required)
        visa_type_id: Optional visa type ID to check (if None, checks all active visa types for jurisdiction)
        enable_ai_reasoning: Whether to run AI reasoning (default: True)
        evaluation_date: Optional ISO format date string to evaluate against (defaults to now)
        
    Returns:
        Dict with eligibility check results:
        - For single visa type: EligibilityCheckResult.to_dict()
        - For multiple visa types: {
            'success': bool,
            'case_id': str,
            'results': List[Dict],  # One per visa type
            'summary': Dict,
            'errors': List[Dict]  # Any errors encountered
          }
        
    Raises:
        Retry: If task should be retried (transient errors)
        MaxRetriesExceeded: If max retries exceeded
    """
    task_start_time = time.time()
    
    try:
        # Validate case_id format
        try:
            uuid.UUID(case_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid case_id format: {case_id}")
            return {
                'success': False,
                'error': 'Invalid case_id format',
                'case_id': case_id
            }
        
        # Validate visa_type_id format if provided
        if visa_type_id:
            try:
                uuid.UUID(visa_type_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid visa_type_id format: {visa_type_id}")
                return {
                    'success': False,
                    'error': 'Invalid visa_type_id format',
                    'case_id': case_id,
                    'visa_type_id': visa_type_id
                }
        
        logger.info(
            f"Starting eligibility check task for case: {case_id}, "
            f"visa_type: {visa_type_id or 'ALL'}, ai_reasoning: {enable_ai_reasoning}, "
            f"retry_count: {self.request.retries}"
        )
        
        # Get case
        case = CaseSelector.get_by_id(case_id)
        if not case:
            error_msg = f"Case {case_id} not found"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'case_id': case_id
            }
        
        # Validate payment requirement early (before expensive operations)
        from payments.helpers.payment_validator import PaymentValidator
        is_valid, error = PaymentValidator.validate_case_has_payment(
            case,
            operation_name="eligibility check task"
        )
        if not is_valid:
            logger.warning(f"Eligibility check task blocked for case {case_id}: {error}")
            return {
                'success': False,
                'error': error,
                'case_id': case_id,
                'visa_type_id': visa_type_id,
                'blocked': True
            }
        
        # Parse evaluation_date if provided
        parsed_evaluation_date = None
        if evaluation_date:
            try:
                from datetime import datetime
                parsed_evaluation_date = datetime.fromisoformat(evaluation_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid evaluation_date format '{evaluation_date}': {e}. Using current date.")
        
        # If visa_type_id provided, check only that visa type
        if visa_type_id:
            return _run_single_visa_type_check(
                case_id=case_id,
                visa_type_id=visa_type_id,
                enable_ai_reasoning=enable_ai_reasoning,
                evaluation_date=parsed_evaluation_date,
                task_start_time=task_start_time
            )
        else:
            # Check all active visa types for the case's jurisdiction
            return _run_multi_visa_type_check(
                case=case,
                enable_ai_reasoning=enable_ai_reasoning,
                evaluation_date=parsed_evaluation_date,
                task_start_time=task_start_time
            )
        
    except Retry:
        # Re-raise retry exceptions
        raise
    except MaxRetriesExceeded:
        logger.error(
            f"Max retries exceeded for eligibility check task (case: {case_id}). "
            f"Task will not be retried again."
        )
        return {
            'success': False,
            'error': 'Max retries exceeded',
            'case_id': case_id,
            'visa_type_id': visa_type_id,
            'retries_exceeded': True
        }
    except Exception as e:
        logger.error(
            f"Unexpected error in eligibility check task for case {case_id}: {e}",
            exc_info=True
        )
        
        # Determine if error is retryable
        retryable_errors = (
            'ConnectionError', 'TimeoutError', 'ServiceUnavailableError',
            'RateLimitError', 'TemporaryError'
        )
        is_retryable = any(err_type in str(type(e).__name__) for err_type in retryable_errors)
        
        if is_retryable and self.request.retries < self.max_retries:
            # Exponential backoff: 60s, 120s, 240s
            countdown = 60 * (2 ** self.request.retries)
            logger.info(
                f"Retrying eligibility check task for case {case_id} "
                f"(attempt {self.request.retries + 1}/{self.max_retries}) "
                f"in {countdown} seconds"
            )
            raise self.retry(exc=e, countdown=countdown, max_retries=self.max_retries)
        else:
            # Non-retryable error or max retries exceeded
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'case_id': case_id,
                'visa_type_id': visa_type_id,
                'retryable': is_retryable
            }


def _run_single_visa_type_check(
    case_id: str,
    visa_type_id: str,
    enable_ai_reasoning: bool,
    evaluation_date: Optional[Any],
    task_start_time: float
) -> Dict[str, Any]:
    """
    Run eligibility check for a single visa type.
    
    Args:
        case_id: UUID of the case
        visa_type_id: UUID of the visa type
        enable_ai_reasoning: Whether to enable AI reasoning
        evaluation_date: Optional evaluation date
        task_start_time: Task start time for metrics
        
    Returns:
        Dict with eligibility check result
    """
    try:
        # Validate visa type exists
        visa_type = VisaTypeSelector.get_by_id(visa_type_id)
        if not visa_type:
            logger.error(f"Visa type {visa_type_id} not found")
            return {
                'success': False,
                'error': 'Visa type not found',
                'case_id': case_id,
                'visa_type_id': visa_type_id
            }
        
        # Run complete eligibility check
        check_result = EligibilityCheckService.run_eligibility_check(
            case_id=case_id,
            visa_type_id=visa_type_id,
            evaluation_date=evaluation_date,
            enable_ai_reasoning=enable_ai_reasoning
        )
        
        # Track metrics
        duration = time.time() - task_start_time
        if check_result.success:
            track_eligibility_check(
                outcome=check_result.outcome,
                requires_review=check_result.requires_human_review,
                conflict_detected=check_result.conflict_detected,
                duration=duration,
                confidence=check_result.confidence
            )
            
            if check_result.conflict_detected:
                track_eligibility_conflict(
                    conflict_type=check_result.conflict_reason or 'unknown'
                )
            
            if check_result.requires_human_review:
                escalation_reason = 'low_confidence' if check_result.confidence < EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD else 'conflict'
                track_auto_escalation(reason=escalation_reason)
        
        result_dict = check_result.to_dict()
        result_dict['task_duration_seconds'] = round(duration, 2)
        result_dict['task_completed_at'] = timezone.now().isoformat()
        
        logger.info(
            f"Eligibility check task completed for case {case_id}, visa {visa_type_id}: "
            f"outcome={check_result.outcome}, duration={duration:.2f}s"
        )
        
        return result_dict
        
    except Exception as e:
        logger.error(
            f"Error in single visa type check (case: {case_id}, visa: {visa_type_id}): {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'case_id': case_id,
            'visa_type_id': visa_type_id
        }


def _run_multi_visa_type_check(
    case: Any,
    enable_ai_reasoning: bool,
    evaluation_date: Optional[Any],
    task_start_time: float
) -> Dict[str, Any]:
    """
    Run eligibility checks for all active visa types in the case's jurisdiction.
    
    Args:
        case: Case instance
        enable_ai_reasoning: Whether to enable AI reasoning
        evaluation_date: Optional evaluation date
        task_start_time: Task start time for metrics
        
    Returns:
        Dict with aggregated results for all visa types
    """
    try:
        # Get jurisdiction
        jurisdiction = case.jurisdiction if hasattr(case, 'jurisdiction') else None
        if not jurisdiction:
            logger.warning(f"Case {case.id} has no jurisdiction - cannot check all visa types")
            return {
                'success': False,
                'error': 'Case has no jurisdiction specified',
                'case_id': str(case.id)
            }
        
        # Get all active visa types for this jurisdiction
        visa_types = VisaTypeSelector.get_by_jurisdiction(jurisdiction)
        if not visa_types.exists():
            logger.warning(f"No active visa types found for jurisdiction {jurisdiction}")
            return {
                'success': False,
                'error': f'No active visa types found for jurisdiction {jurisdiction}',
                'case_id': str(case.id),
                'jurisdiction': jurisdiction
            }
        
        visa_type_list = list(visa_types)
        logger.info(
            f"Checking {len(visa_type_list)} visa types for case {case.id}, "
            f"jurisdiction: {jurisdiction}"
        )
        
        # Limit number of visa types to prevent resource exhaustion
        MAX_VISA_TYPES = 20
        if len(visa_type_list) > MAX_VISA_TYPES:
            logger.warning(
                f"Too many visa types ({len(visa_type_list)}) for case {case.id}. "
                f"Limiting to {MAX_VISA_TYPES}."
            )
            visa_type_list = visa_type_list[:MAX_VISA_TYPES]
        
        # Run eligibility checks for each visa type
        results = []
        errors = []
        all_requires_review = False
        low_confidence_count = 0
        conflict_count = 0
        
        for visa_type in visa_type_list:
            try:
                check_result = EligibilityCheckService.run_eligibility_check(
                    case_id=str(case.id),
                    visa_type_id=str(visa_type.id),
                    evaluation_date=evaluation_date,
                    enable_ai_reasoning=enable_ai_reasoning
                )
                
                if check_result.success:
                    result_dict = check_result.to_dict()
                    result_dict['visa_code'] = visa_type.code
                    result_dict['visa_name'] = visa_type.name
                    results.append(result_dict)
                    
                    # Track aggregate flags
                    if check_result.requires_human_review:
                        all_requires_review = True
                    
                    if check_result.confidence < EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD:
                        low_confidence_count += 1
                    
                    if check_result.conflict_detected:
                        conflict_count += 1
                else:
                    errors.append({
                        'visa_type_id': str(visa_type.id),
                        'visa_code': visa_type.code,
                        'visa_name': visa_type.name,
                        'error': check_result.error or 'Unknown error',
                        'warnings': check_result.warnings
                    })
                    logger.warning(
                        f"Eligibility check failed for case {case.id}, "
                        f"visa {visa_type.code}: {check_result.error}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Error checking visa type {visa_type.id} for case {case.id}: {e}",
                    exc_info=True
                )
                errors.append({
                    'visa_type_id': str(visa_type.id),
                    'visa_code': visa_type.code,
                    'visa_name': visa_type.name,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                continue
        
        # Update case status if at least one check succeeded
        if results:
            try:
                updated_case, error_msg, http_status = CaseService.update_case(
                    str(case.id),
                    updated_by_id=None,  # System update
                    reason='Eligibility checks completed (multi-visa-type)',
                    status='evaluated'
                )
                if not updated_case and error_msg:
                    logger.warning(f"Failed to update case status: {error_msg}")
            except Exception as e:
                logger.error(f"Error updating case status: {e}", exc_info=True)
                # Continue - don't fail the entire task if status update fails
        
        # Track aggregate metrics
        duration = time.time() - task_start_time
        if results:
            # Track metrics for successful checks
            for result in results:
                track_eligibility_check(
                    outcome=result.get('outcome', 'unknown'),
                    requires_review=result.get('requires_human_review', False),
                    conflict_detected=result.get('conflict_detected', False),
                    duration=duration / len(results),  # Average duration per check
                    confidence=result.get('confidence', 0.0)
                )
        
        # Build response
        response = {
            'success': len(results) > 0,  # Success if at least one check succeeded
            'case_id': str(case.id),
            'jurisdiction': jurisdiction,
            'results': results,
            'summary': {
                'total_checked': len(visa_type_list),
                'successful': len(results),
                'failed': len(errors),
                'requires_human_review': all_requires_review,
                'low_confidence_count': low_confidence_count,
                'conflict_count': conflict_count
            },
            'task_duration_seconds': round(duration, 2),
            'task_completed_at': timezone.now().isoformat()
        }
        
        if errors:
            response['errors'] = errors
        
        logger.info(
            f"Multi-visa-type eligibility check completed for case {case.id}: "
            f"{len(results)} succeeded, {len(errors)} failed, duration={duration:.2f}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error in multi-visa-type check for case {case.id}: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'case_id': str(case.id),
            'jurisdiction': case.jurisdiction if hasattr(case, 'jurisdiction') else None
        }

