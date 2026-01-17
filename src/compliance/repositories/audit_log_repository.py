from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
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
                thread=thread,
                version=1,
                is_deleted=False,
            )
            audit_log.full_clean()
            audit_log.save()
            return audit_log

    @staticmethod
    def update_audit_log(audit_log: AuditLog, version: int = None, **fields) -> AuditLog:
        """
        Update an audit log entry with optimistic locking.

        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(audit_log, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in AuditLog._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = timezone.now()

            updated_count = AuditLog.objects.filter(
                id=audit_log.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = AuditLog.objects.filter(id=audit_log.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Audit log not found.")
                raise ValidationError(
                    f"Audit log was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return AuditLog.objects.get(id=audit_log.id)

    @staticmethod
    def soft_delete_audit_log(audit_log: AuditLog, version: int = None) -> AuditLog:
        """Soft delete an audit log entry with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(audit_log, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = AuditLog.objects.filter(
                id=audit_log.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = AuditLog.objects.filter(id=audit_log.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Audit log not found.")
                raise ValidationError(
                    f"Audit log was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return AuditLog.objects.get(id=audit_log.id)

    @staticmethod
    def delete_audit_log(audit_log: AuditLog, version: int = None) -> AuditLog:
        """
        Delete an audit log entry.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        return AuditLogRepository.soft_delete_audit_log(audit_log, version=version)
