from django.db import transaction
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
                **fields
            )
            audit_log.full_clean()
            audit_log.save()
            return audit_log

    @staticmethod
    def delete_audit_log(audit_log: CallAuditLog):
        """Delete an audit log entry."""
        with transaction.atomic():
            audit_log.delete()
