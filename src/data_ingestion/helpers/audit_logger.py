"""
Audit logging utilities for rule parsing operations.

Provides structured audit logging for compliance and debugging.
Note: All database writes are delegated to RuleParsingAuditLogRepository.

This is distinct from compliance.models.AuditLog which is for general
application logging. This logger handles domain-specific audit logs
for rule parsing workflow events.
"""

import logging
from typing import Dict, Optional, Any
from data_ingestion.models.audit_log import RuleParsingAuditLog
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.repositories.audit_log_repository import RuleParsingAuditLogRepository

logger = logging.getLogger('django')


class RuleParsingAuditLogger:
    """
    Audit logger for rule parsing operations.
    
    Logs all rule parsing workflow events to database for compliance and debugging.
    All database writes are handled by RuleParsingAuditLogRepository.
    
    This is distinct from compliance.models.AuditLog which captures
    general application logs from Python's logging system.
    """
    
    @staticmethod
    def log_action(
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
    ) -> Optional[RuleParsingAuditLog]:
        """
        Log an audit event.
        
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
            Created audit log entry or None if creation failed
        """
        try:
            audit_log = RuleParsingAuditLogRepository.create_audit_log(
                document_version=document_version,
                action=action,
                status=status,
                message=message,
                metadata=metadata,
                error_type=error_type,
                error_message=error_message,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Also log to standard logger
            log_message = f"AUDIT: {action} - {status} - {document_version.id}"
            if message:
                log_message += f" - {message}"
            
            if status == 'failure':
                logger.error(log_message, extra={'audit_log_id': str(audit_log.id)})
            elif status == 'warning':
                logger.warning(log_message, extra={'audit_log_id': str(audit_log.id)})
            else:
                logger.info(log_message, extra={'audit_log_id': str(audit_log.id)})
            
            return audit_log
            
        except Exception as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            # Return None to indicate failure, but don't raise
            return None
    
    @staticmethod
    def log_parse_started(
        document_version: DocumentVersion,
        metadata: Optional[Dict[str, Any]] = None,
        user=None
    ) -> RuleParsingAuditLog:
        """Log that parsing has started."""
        return RuleParsingAuditLogger.log_action(
            document_version=document_version,
            action='parse_started',
            status='success',
            message=f"Started parsing document version {document_version.id}",
            metadata=metadata,
            user=user
        )
    
    @staticmethod
    def log_parse_completed(
        document_version: DocumentVersion,
        rules_created: int,
        metadata: Optional[Dict[str, Any]] = None,
        user=None
    ) -> RuleParsingAuditLog:
        """Log that parsing has completed successfully."""
        metadata = metadata or {}
        metadata['rules_created'] = rules_created
        
        return RuleParsingAuditLogger.log_action(
            document_version=document_version,
            action='parse_completed',
            status='success',
            message=f"Completed parsing: {rules_created} rules created",
            metadata=metadata,
            user=user
        )
    
    @staticmethod
    def log_parse_failed(
        document_version: DocumentVersion,
        error_type: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
        user=None
    ) -> RuleParsingAuditLog:
        """Log that parsing has failed."""
        return RuleParsingAuditLogger.log_action(
            document_version=document_version,
            action='parse_failed',
            status='failure',
            message=f"Parsing failed: {error_message}",
            metadata=metadata,
            error_type=error_type,
            error_message=error_message,
            user=user
        )
    
    @staticmethod
    def log_pii_detected(
        document_version: DocumentVersion,
        pii_count: int,
        pii_types: Dict[str, int],
        user=None
    ) -> RuleParsingAuditLog:
        """Log that PII was detected and redacted."""
        return RuleParsingAuditLogger.log_action(
            document_version=document_version,
            action='pii_detected',
            status='success',
            message=f"Detected and redacted {pii_count} PII items",
            metadata={
                'pii_count': pii_count,
                'pii_types': pii_types
            },
            user=user
        )
    
    @staticmethod
    def log_rate_limit_wait(
        document_version: DocumentVersion,
        wait_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RuleParsingAuditLog:
        """Log rate limit wait."""
        metadata = metadata or {}
        metadata['wait_time_seconds'] = wait_time
        
        return RuleParsingAuditLogger.log_action(
            document_version=document_version,
            action='rate_limit_wait',
            status='warning',
            message=f"Rate limit: waited {wait_time:.2f}s",
            metadata=metadata
        )
    
    @staticmethod
    def log_cache_hit(
        document_version: DocumentVersion,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RuleParsingAuditLog:
        """Log cache hit."""
        return RuleParsingAuditLogger.log_action(
            document_version=document_version,
            action='cache_hit',
            status='success',
            message="Used cached LLM response",
            metadata=metadata
        )
