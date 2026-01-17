from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_calls.models.call_audit_log import CallAuditLog


class CallAuditLogRepository:
    """Repository for CallAuditLog write operations."""

    @staticmethod
    def create_audit_log(call_session, event_type: str, description: str, **fields):
        """Create a new audit log entry."""
        with transaction.atomic():
            audit_log = CallAuditLog.objects.create(
                call_session=call_session,
                event_type=event_type,
                description=description,
                version=1,
                is_deleted=False,
                **fields
            )
            audit_log.full_clean()
            audit_log.save()
            return audit_log

    @staticmethod
    def soft_delete_audit_log(audit_log: CallAuditLog, version: int = None) -> CallAuditLog:
        """Soft delete an audit log entry with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(audit_log, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = CallAuditLog.objects.filter(
                id=audit_log.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CallAuditLog.objects.filter(id=audit_log.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Audit log entry not found.")
                raise ValidationError(
                    f"Audit log entry was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CallAuditLog.objects.get(id=audit_log.id)

    @staticmethod
    def delete_audit_log(audit_log: CallAuditLog, version: int = None):
        """
        Delete an audit log entry.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        return CallAuditLogRepository.soft_delete_audit_log(audit_log, version=version)
