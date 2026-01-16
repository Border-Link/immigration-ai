from immigration_cases.models.case_status_history import CaseStatusHistory
from immigration_cases.models.case import Case

class CaseStatusHistorySelector:
    """Selector for CaseStatusHistory read operations."""

    @staticmethod
    def get_all():
        """Get all status history entries."""
        return CaseStatusHistory.objects.select_related(
            'case',
            'case__user',
            'changed_by'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get status history by case."""
        return CaseStatusHistory.objects.select_related(
            'case',
            'case__user',
            'changed_by'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_id(history_id):
        """Get status history by ID."""
        return CaseStatusHistory.objects.select_related(
            'case',
            'case__user',
            'changed_by'
        ).get(id=history_id)

    @staticmethod
    def get_by_case_id(case_id: str):
        """Get status history by case ID."""
        return CaseStatusHistory.objects.select_related(
            'case',
            'case__user',
            'changed_by'
        ).filter(case_id=case_id).order_by('-created_at')

    @staticmethod
    def get_none():
        """Return an empty queryset."""
        return CaseStatusHistory.objects.none()
