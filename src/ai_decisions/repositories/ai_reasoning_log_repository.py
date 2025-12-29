from django.db import transaction
from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from immigration_cases.models.case import Case


class AIReasoningLogRepository:
    """Repository for AIReasoningLog write operations."""

    @staticmethod
    def create_reasoning_log(case: Case, prompt: str, response: str, model_name: str,
                            tokens_used: int = None):
        """Create a new AI reasoning log."""
        with transaction.atomic():
            log = AIReasoningLog.objects.create(
                case=case,
                prompt=prompt,
                response=response,
                model_name=model_name,
                tokens_used=tokens_used
            )
            log.full_clean()
            log.save()
            return log

    @staticmethod
    def update_reasoning_log(log: AIReasoningLog, **fields):
        """Update reasoning log fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(log, key):
                    setattr(log, key, value)
            log.full_clean()
            log.save()
            return log

    @staticmethod
    def delete_reasoning_log(log: AIReasoningLog):
        """Delete an AI reasoning log."""
        with transaction.atomic():
            log.delete()

