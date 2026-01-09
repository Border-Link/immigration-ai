"""
Repository for RuleParsingAuditLog write operations.

Note: This is distinct from compliance.models.AuditLog which is for
general application logging. This repository handles domain-specific
audit logs for rule parsing operations.
"""

from typing import Optional, Dict, Any
from django.db import transaction
from data_ingestion.models.audit_log import RuleParsingAuditLog
from data_ingestion.models.document_version import DocumentVersion


class RuleParsingAuditLogRepository:
    """Repository for RuleParsingAuditLog write operations."""

    @staticmethod
    def create_audit_log(
        document_version: DocumentVersion,
        action: str,
        status: str,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        user=None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RuleParsingAuditLog:
        """
        Create a new audit log entry.
        
        Args:
            document_version: Document version being processed
            action: Action type (from ACTION_CHOICES)
            status: Status (success, failure, warning)
            message: Human-readable message
            metadata: Additional metadata dict
            error_type: Error type if failed
            error_message: Error message if failed
            user: User who triggered the action
            ip_address: IP address of request
            user_agent: User agent of request
            
        Returns:
            Created audit log entry
        """
        with transaction.atomic():
            audit_log = RuleParsingAuditLog.objects.create(
                document_version=document_version,
                action=action,
                status=status,
                message=message,
                metadata=metadata or {},
                error_type=error_type,
                error_message=error_message,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            audit_log.full_clean()
            audit_log.save()
            return audit_log
