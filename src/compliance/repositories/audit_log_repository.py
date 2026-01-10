from django.db import transaction
from compliance.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for AuditLog write operations."""

    @staticmethod
    def create_audit_log(level: str, logger_name: str, message: str, 
                        pathname: str = None, lineno: int = None, 
                        func_name: str = None, process: int = None, 
                        thread: str = None):
        """Create a new audit log entry."""
        with transaction.atomic():
            audit_log = AuditLog.objects.create(
                level=level,
                logger_name=logger_name,
                message=message,
                pathname=pathname,
                lineno=lineno,
                func_name=func_name,
                process=process,
                thread=thread
            )
            audit_log.full_clean()
            audit_log.save()
            return audit_log

    @staticmethod
    def delete_audit_log(audit_log):
        """Delete an audit log entry."""
        with transaction.atomic():
            audit_log.delete()
            return True
