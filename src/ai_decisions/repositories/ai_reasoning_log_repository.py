from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
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
                tokens_used=tokens_used,
                version=1,
                is_deleted=False,
            )
            log.full_clean()
            log.save()
            return log

    @staticmethod
    def update_reasoning_log(log: AIReasoningLog, version: int = None, **fields):
        """Update reasoning log fields with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(log, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed = {"prompt", "response", "model_name", "tokens_used"}
            update_fields = {k: v for k, v in fields.items() if k in allowed}
            update_fields["updated_at"] = timezone.now()

            updated = AIReasoningLog.objects.filter(
                id=log.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated != 1:
                current_version = AIReasoningLog.objects.filter(id=log.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("AI reasoning log not found.")
                raise ValidationError(
                    f"AI reasoning log was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return AIReasoningLog.objects.get(id=log.id)

    @staticmethod
    def soft_delete_reasoning_log(log: AIReasoningLog, version: int = None) -> AIReasoningLog:
        """Soft delete an AI reasoning log with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(log, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated = AIReasoningLog.objects.filter(
                id=log.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated != 1:
                current_version = AIReasoningLog.objects.filter(id=log.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("AI reasoning log not found.")
                raise ValidationError(
                    f"AI reasoning log was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return AIReasoningLog.objects.get(id=log.id)

    @staticmethod
    def delete_reasoning_log(log: AIReasoningLog, version: int = None):
        """
        Delete an AI reasoning log.

        CRITICAL: deletion must be soft-delete.
        """
        return AIReasoningLogRepository.soft_delete_reasoning_log(log, version=version)

