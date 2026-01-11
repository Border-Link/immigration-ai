from django.db import transaction
from immigration_cases.models.case import Case
from immigration_cases.models.case_status_history import CaseStatusHistory
from django.conf import settings

class CaseStatusHistoryRepository:
    """Repository for CaseStatusHistory write operations."""

    @staticmethod
    def create_status_history(case: Case, previous_status: str, new_status: str, changed_by=None, reason: str = None, metadata: dict = None):
        """Create a new case status history entry."""
        with transaction.atomic():
            history = CaseStatusHistory.objects.create(
                case=case,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
                reason=reason,
                metadata=metadata
            )
            history.full_clean()
            history.save()
            return history
