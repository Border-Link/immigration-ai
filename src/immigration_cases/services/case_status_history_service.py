from __future__ import annotations

import logging
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from main_system.utils.cache_utils import cache_result
from immigration_cases.selectors.case_status_history_selector import CaseStatusHistorySelector
from immigration_cases.selectors.case_selector import CaseSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    # Tie status-history caching to the Case namespace to ensure updates invalidate history views.
    return "cases"

class CaseStatusHistoryService:
    """Service for CaseStatusHistory business logic."""

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")  # 5 minutes - history list changes when status changes
    def get_all():
        """Get all case status histories."""
        try:
            return CaseStatusHistorySelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all case status histories: {e}")
            return CaseStatusHistorySelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache history by case
    def get_by_case_id(case_id: str):
        """Get status histories for a specific case by ID."""
        try:
            return CaseStatusHistorySelector.get_by_case_id(case_id)
        except Exception as e:
            logger.error(f"Error fetching status histories for case {case_id}: {e}")
            return CaseStatusHistorySelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['history_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache history entry by ID
    def get_by_id(history_id: str) -> Optional[CaseStatusHistory]:
        """Get case status history by ID."""
        try:
            return CaseStatusHistorySelector.get_by_id(history_id)
        except ObjectDoesNotExist:
            logger.error(f"Case status history {history_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching case status history {history_id}: {e}")
            return None
