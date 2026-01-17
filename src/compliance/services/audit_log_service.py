import logging
import time
from typing import Optional
from compliance.models.audit_log import AuditLog
from compliance.repositories.audit_log_repository import AuditLogRepository
from compliance.selectors.audit_log_selector import AuditLogSelector
from compliance.helpers.metrics import track_audit_log_creation

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
            return AuditLog.objects.none()

    @staticmethod
    def get_by_level(level: str):
        """Get audit logs by level."""
        try:
            return AuditLogSelector.get_by_level(level)
        except Exception as e:
            logger.error(f"Error fetching audit logs by level {level}: {e}")
            return AuditLog.objects.none()

    @staticmethod
    def get_by_logger_name(logger_name: str):
        """Get audit logs by logger name."""
        try:
            return AuditLogSelector.get_by_logger_name(logger_name)
        except Exception as e:
            logger.error(f"Error fetching audit logs by logger name {logger_name}: {e}")
            return AuditLog.objects.none()

    @staticmethod
    def get_by_id(log_id: str) -> Optional[AuditLog]:
        """Get audit log by ID."""
        try:
            log = AuditLogSelector.get_by_id(log_id)
            if not log:
                logger.error(f"Audit log {log_id} not found")
                return None
            return log
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
            return AuditLog.objects.none()

    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Get audit logs within a date range."""
        try:
            return AuditLogSelector.get_by_date_range(start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching audit logs by date range: {e}")
            return AuditLog.objects.none()

    @staticmethod
    def create_audit_log(level: str, logger_name: str, message: str,
                        pathname: str = None, lineno: int = None,
                        func_name: str = None, process: int = None,
                        thread: str = None, user=None):
        """
        Create an audit log entry.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            logger_name: Name of the logger/module
            message: Audit log message
            pathname: Path to the file where the log was created
            lineno: Line number where the log was created
            func_name: Function name where the log was created
            process: Process ID
            thread: Thread ID
            user: User object (optional, for user attribution)
        
        Returns:
            AuditLog instance or None if creation failed
        """
        start_time = time.time()
        try:
            audit_log = AuditLogRepository.create_audit_log(
                level=level,
                logger_name=logger_name,
                message=message,
                pathname=pathname,
                lineno=lineno,
                func_name=func_name,
                process=process,
                thread=thread
            )
            
            # Track metrics
            duration = time.time() - start_time
            track_audit_log_creation(
                level=level,
                logger_name=logger_name,
                duration=duration
            )
            
            return audit_log
        except Exception as e:
            logger.error(f"Error creating audit log: {e}", exc_info=True)
            return None

    @staticmethod
    def update_audit_log(log_id: str, version: int = None, **fields) -> Optional[AuditLog]:
        """Update audit log fields with optimistic locking."""
        try:
            log = AuditLogSelector.get_by_id(log_id)
            if not log:
                logger.error(f"Audit log {log_id} not found")
                return None
            return AuditLogRepository.update_audit_log(log, version=version, **fields)
        except Exception as e:
            logger.error(f"Error updating audit log {log_id}: {e}")
            return None

    @staticmethod
    def delete_audit_log(log_id: str, version: int = None) -> bool:
        """Soft delete an audit log entry with optimistic locking."""
        try:
            log = AuditLogSelector.get_by_id(log_id)
            if not log:
                logger.error(f"Audit log {log_id} not found")
                return False
            AuditLogRepository.delete_audit_log(log, version=version)
            return True
        except Exception as e:
            logger.error(f"Error deleting audit log {log_id}: {e}")
            return False
