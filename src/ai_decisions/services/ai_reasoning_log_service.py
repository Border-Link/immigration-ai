import logging
from typing import Optional
from helpers.cache_utils import cache_result
from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from ai_decisions.repositories.ai_reasoning_log_repository import AIReasoningLogRepository
from ai_decisions.selectors.ai_reasoning_log_selector import AIReasoningLogSelector
from immigration_cases.selectors.case_selector import CaseSelector

logger = logging.getLogger('django')


class AIReasoningLogService:
    """Service for AIReasoningLog business logic."""

    @staticmethod
    def create_reasoning_log(case_id: str, prompt: str, response: str, model_name: str,
                            tokens_used: int = None) -> Optional[AIReasoningLog]:
        """Create a new AI reasoning log."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return AIReasoningLogRepository.create_reasoning_log(
                case=case,
                prompt=prompt,
                response=response,
                model_name=model_name,
                tokens_used=tokens_used
            )
        except Exception as e:
            logger.error(f"Error creating AI reasoning log: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - logs change when new reasoning occurs
    def get_all():
        """Get all AI reasoning logs."""
        try:
            return AIReasoningLogSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all AI reasoning logs: {e}")
            return AIReasoningLogSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])  # 5 minutes - cache logs by case
    def get_by_case(case_id: str):
        """Get reasoning logs by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return AIReasoningLogSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching reasoning logs for case {case_id}: {e}")
            return AIReasoningLogSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['log_id'])  # 10 minutes - cache log by ID
    def get_by_id(log_id: str) -> Optional[AIReasoningLog]:
        """Get reasoning log by ID."""
        try:
            return AIReasoningLogSelector.get_by_id(log_id)
        except AIReasoningLog.DoesNotExist:
            logger.error(f"AI reasoning log {log_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching reasoning log {log_id}: {e}")
            return None
    
    @staticmethod
    @cache_result(timeout=300, keys=['model_name'])  # 5 minutes - cache logs by model
    def get_by_model(model_name: str):
        """Get reasoning logs by model name."""
        try:
            return AIReasoningLogSelector.get_by_model(model_name)
        except Exception as e:
            logger.error(f"Error fetching reasoning logs for model {model_name}: {e}")
            return AIReasoningLogSelector.get_none()

    @staticmethod
    def update_reasoning_log(log_id: str, **fields) -> Optional[AIReasoningLog]:
        """Update reasoning log fields."""
        try:
            log = AIReasoningLogSelector.get_by_id(log_id)
            return AIReasoningLogRepository.update_reasoning_log(log, **fields)
        except AIReasoningLog.DoesNotExist:
            logger.error(f"AI reasoning log {log_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating reasoning log {log_id}: {e}")
            return None

    @staticmethod
    def delete_reasoning_log(log_id: str) -> bool:
        """Delete an AI reasoning log."""
        try:
            log = AIReasoningLogSelector.get_by_id(log_id)
            AIReasoningLogRepository.delete_reasoning_log(log)
            return True
        except AIReasoningLog.DoesNotExist:
            logger.error(f"AI reasoning log {log_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting reasoning log {log_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(case_id: str = None, model_name: str = None, min_tokens: int = None, 
                       date_from=None, date_to=None):
        """Get AI reasoning logs with filters."""
        try:
            if case_id:
                logs = AIReasoningLogService.get_by_case(case_id)
            elif model_name:
                logs = AIReasoningLogSelector.get_by_model(model_name)
            else:
                logs = AIReasoningLogSelector.get_all()
            
            # Apply additional filters
            if min_tokens is not None:
                logs = logs.filter(tokens_used__gte=min_tokens)
            if date_from:
                logs = logs.filter(created_at__gte=date_from)
            if date_to:
                logs = logs.filter(created_at__lte=date_to)
            
            return logs
        except Exception as e:
            logger.error(f"Error fetching filtered AI reasoning logs: {e}")
            return AIReasoningLogSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get AI reasoning log statistics."""
        try:
            return AIReasoningLogSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting AI reasoning log statistics: {e}")
            return {}
