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
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_document_version(document_version: DocumentVersion):
        """Get audit logs by document version."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(document_version=document_version, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_action(action: str):
        """Get audit logs by action type."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(action=action, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str):
        """Get audit logs by status."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(status=status, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_error_type(error_type: str):
        """Get audit logs by error type."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'user'
        ).filter(error_type=error_type, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(audit_log_id):
        """Get audit log by ID."""
        return RuleParsingAuditLog.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source',
            'user'
        ).filter(id=audit_log_id, is_deleted=False).first()

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return RuleParsingAuditLog.objects.none()

    @staticmethod
    def get_by_filters(action: str = None, status: str = None, error_type: str = None, 
                       user_id: str = None, document_version=None, date_from=None, date_to=None):
        """Get audit logs with filters."""
        if action:
            queryset = RuleParsingAuditLogSelector.get_by_action(action)
        elif status:
            queryset = RuleParsingAuditLogSelector.get_by_status(status)
        elif error_type:
            queryset = RuleParsingAuditLogSelector.get_by_error_type(error_type)
        elif document_version:
            queryset = RuleParsingAuditLogSelector.get_by_document_version(document_version)
        else:
            queryset = RuleParsingAuditLogSelector.get_all()
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get audit log statistics."""
        from django.db.models import Count
        
        queryset = RuleParsingAuditLog.objects.filter(is_deleted=False)
        
        total_audit_logs = queryset.count()
        logs_by_action = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        logs_by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        error_logs = queryset.exclude(
            error_type__isnull=True
        ).count()
        
        return {
            'total': total_audit_logs,
            'with_errors': error_logs,
            'by_action': list(logs_by_action),
            'by_status': list(logs_by_status),
        }
