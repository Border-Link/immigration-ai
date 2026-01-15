"""
Service for RuleParsingAuditLog business logic.
"""
import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result
from data_ingestion.models.audit_log import RuleParsingAuditLog
from data_ingestion.selectors.audit_log_selector import RuleParsingAuditLogSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "rule_parsing_audit_logs"


class RuleParsingAuditLogService:
    """Service for RuleParsingAuditLog business logic."""

    @staticmethod
    def get_all():
        """Get all audit logs."""
        try:
            return RuleParsingAuditLogSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all audit logs: {e}")
            return RuleParsingAuditLogSelector.get_none()

    @staticmethod
    def get_by_action(action: str):
        """Get audit logs by action type."""
        try:
            return RuleParsingAuditLogSelector.get_by_action(action)
        except Exception as e:
            logger.error(f"Error fetching audit logs by action {action}: {e}")
            return RuleParsingAuditLogSelector.get_none()

    @staticmethod
    def get_by_status(status: str):
        """Get audit logs by status."""
        try:
            return RuleParsingAuditLogSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching audit logs by status {status}: {e}")
            return RuleParsingAuditLogSelector.get_none()

    @staticmethod
    def get_by_error_type(error_type: str):
        """Get audit logs by error type."""
        try:
            return RuleParsingAuditLogSelector.get_by_error_type(error_type)
        except Exception as e:
            logger.error(f"Error fetching audit logs by error type {error_type}: {e}")
            return RuleParsingAuditLogSelector.get_none()

    @staticmethod
    def get_by_document_version(document_version_id: str):
        """Get audit logs by document version ID."""
        try:
            from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
            document_version = DocumentVersionSelector.get_by_id(document_version_id)
            if not document_version:
                return RuleParsingAuditLogSelector.get_none()
            return RuleParsingAuditLogSelector.get_by_document_version(document_version)
        except Exception as e:
            logger.error(f"Error fetching audit logs for document version {document_version_id}: {e}")
            return RuleParsingAuditLogSelector.get_none()

    @staticmethod
    def get_by_id(audit_log_id: str) -> Optional[RuleParsingAuditLog]:
        """Get audit log by ID."""
        try:
            return RuleParsingAuditLogSelector.get_by_id(audit_log_id)
        except RuleParsingAuditLog.DoesNotExist:
            logger.error(f"Audit log {audit_log_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching audit log {audit_log_id}: {e}")
            return None

    @staticmethod
    def get_by_filters(action: str = None, status: str = None, error_type: str = None, 
                       user_id: str = None, document_version_id: str = None, 
                       date_from=None, date_to=None):
        """Get audit logs with filters."""
        try:
            from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
            
            document_version = None
            if document_version_id:
                document_version = DocumentVersionSelector.get_by_id(document_version_id)
            
            return RuleParsingAuditLogSelector.get_by_filters(
                action=action,
                status=status,
                error_type=error_type,
                user_id=user_id,
                document_version=document_version,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error fetching filtered audit logs: {e}")
            return RuleParsingAuditLogSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get audit log statistics."""
        try:
            return RuleParsingAuditLogSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting audit log statistics: {e}")
            return {}
