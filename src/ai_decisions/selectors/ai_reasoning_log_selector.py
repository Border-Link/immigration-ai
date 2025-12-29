from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from immigration_cases.models.case import Case


class AIReasoningLogSelector:
    """Selector for AIReasoningLog read operations."""

    @staticmethod
    def get_all():
        """Get all AI reasoning logs."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get reasoning logs by case."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_model(model_name: str):
        """Get reasoning logs by model name."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(model_name=model_name).order_by('-created_at')

    @staticmethod
    def get_by_id(log_id):
        """Get reasoning log by ID."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).get(id=log_id)

