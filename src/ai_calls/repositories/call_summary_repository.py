from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_calls.models.call_summary import CallSummary


class CallSummaryRepository:
    """Repository for CallSummary write operations."""

    @staticmethod
    def create_call_summary(call_session, summary_text: str, total_turns: int, total_duration_seconds: int, **fields):
        """Create a new call summary."""
        with transaction.atomic():
            summary = CallSummary.objects.create(
                call_session=call_session,
                summary_text=summary_text,
                total_turns=total_turns,
                total_duration_seconds=total_duration_seconds,
                version=1,
                is_deleted=False,
                **fields
            )
            summary.full_clean()
            summary.save()
            return summary

    @staticmethod
    def update_call_summary(summary: CallSummary, version: int = None, **fields):
        """
        Update call summary fields with optimistic locking.

        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(summary, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in CallSummary._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = timezone.now()

            updated_count = CallSummary.objects.filter(
                id=summary.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CallSummary.objects.filter(id=summary.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Call summary not found.")
                raise ValidationError(
                    f"Call summary was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CallSummary.objects.get(id=summary.id)

    @staticmethod
    def soft_delete_call_summary(summary: CallSummary, version: int = None) -> CallSummary:
        """Soft delete a call summary with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(summary, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = CallSummary.objects.filter(
                id=summary.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CallSummary.objects.filter(id=summary.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Call summary not found.")
                raise ValidationError(
                    f"Call summary was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CallSummary.objects.get(id=summary.id)

    @staticmethod
    def delete_call_summary(summary: CallSummary, version: int = None):
        """
        Delete a call summary.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        return CallSummaryRepository.soft_delete_call_summary(summary, version=version)
