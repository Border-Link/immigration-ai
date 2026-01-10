import logging
from typing import Optional
from compliance.models.audit_log import AuditLog
from compliance.repositories.audit_log_repository import AuditLogRepository
from compliance.selectors.audit_log_selector import AuditLogSelector

logger = logging.getLogger('django')


class AuditLogService:
    """Service for AuditLog business logic."""

    @staticmethod
    def get_all():
        """Get all audit logs."""
        try:
            return AuditLogSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all audit logs: {e}")
            return AuditLogSelector.get_none()

    @staticmethod
    def get_by_level(level: str):
        """Get audit logs by level."""
        try:
            return AuditLogSelector.get_by_level(level)
        except Exception as e:
            logger.error(f"Error fetching audit logs by level {level}: {e}")
            return AuditLogSelector.get_none()

    @staticmethod
    def get_by_logger_name(logger_name: str):
        """Get audit logs by logger name."""
        try:
            return AuditLogSelector.get_by_logger_name(logger_name)
        except Exception as e:
            logger.error(f"Error fetching audit logs by logger name {logger_name}: {e}")
            return AuditLogSelector.get_none()

    @staticmethod
    def get_by_id(log_id: str) -> Optional[AuditLog]:
        """Get audit log by ID."""
        try:
            return AuditLogSelector.get_by_id(log_id)
        except AuditLog.DoesNotExist:
            logger.error(f"Audit log {log_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching audit log {log_id}: {e}")
            return None

    @staticmethod
    def get_recent(limit: int = 100):
        """Get recent audit logs."""
        try:
            return AuditLogSelector.get_recent(limit)
        except Exception as e:
            logger.error(f"Error fetching recent audit logs: {e}")
            return AuditLogSelector.get_none()

    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Get audit logs within a date range."""
        try:
            return AuditLogSelector.get_by_date_range(start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching audit logs by date range: {e}")
            return AuditLogSelector.get_none()

    @staticmethod
    def get_by_filters(level: str = None, logger_name: str = None, date_from=None, date_to=None, limit: int = None):
        """Get audit logs with filters."""
        try:
            return AuditLogSelector.get_by_filters(
                level=level,
                logger_name=logger_name,
                date_from=date_from,
                date_to=date_to,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error fetching filtered audit logs: {e}")
            return AuditLogSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get audit log statistics."""
        try:
            return AuditLogSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting audit log statistics: {e}")
            return {}

    @staticmethod
    def delete_audit_log(log_id: str) -> bool:
        """Delete an audit log."""
        try:
            audit_log = AuditLogSelector.get_by_id(log_id)
            AuditLogRepository.delete_audit_log(audit_log)
            return True
        except AuditLog.DoesNotExist:
            logger.error(f"Audit log {log_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting audit log {log_id}: {e}")
            return False

