"""
Selector for RuleParsingAuditLog read operations.

Note: This is distinct from compliance.selectors.AuditLogSelector which is for
general application logging. This selector handles domain-specific
audit logs for rule parsing operations.
"""

from data_ingestion.models.audit_log import RuleParsingAuditLog
from data_ingestion.models.document_version import DocumentVersion
from typing import Optional


class RuleParsingAuditLogSelector:
    """Selector for RuleParsingAuditLog read operations."""

    @staticmethod
    def get_all():
        """Get all audit logs."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source',
            'user'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_document_version(document_version: DocumentVersion):
        """Get audit logs by document version."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(document_version=document_version).order_by('-created_at')

    @staticmethod
    def get_by_action(action: str):
        """Get audit logs by action type."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(action=action).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str):
        """Get audit logs by status."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(status=status).order_by('-created_at')

    @staticmethod
    def get_by_error_type(error_type: str):
        """Get audit logs by error type."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(error_type=error_type).order_by('-created_at')

    @staticmethod
    def get_by_id(audit_log_id):
        """Get audit log by ID."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source',
            'user'
        ).get(id=audit_log_id)
