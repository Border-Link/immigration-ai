import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result
from immigration_cases.models.case_status_history import CaseStatusHistory
from immigration_cases.selectors.case_status_history_selector import CaseStatusHistorySelector
from immigration_cases.selectors.case_selector import CaseSelector

logger = logging.getLogger('django')

class CaseStatusHistoryService:
    """Service for CaseStatusHistory business logic."""

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - history list changes when status changes
    def get_all():
        """Get all case status histories."""
        try:
            return CaseStatusHistorySelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all case status histories: {e}")
            return CaseStatusHistory.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])  # 5 minutes - cache history by case
    def get_by_case_id(case_id: str):
        """Get status histories for a specific case by ID."""
        try:
            return CaseStatusHistorySelector.get_by_case_id(case_id)
        except Exception as e:
            logger.error(f"Error fetching status histories for case {case_id}: {e}")
            return CaseStatusHistory.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['history_id'])  # 10 minutes - cache history entry by ID
    def get_by_id(history_id: str) -> Optional[CaseStatusHistory]:
        """Get case status history by ID."""
        try:
            return CaseStatusHistorySelector.get_by_id(history_id)
        except CaseStatusHistory.DoesNotExist:
            logger.error(f"Case status history {history_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching case status history {history_id}: {e}")
            return None
