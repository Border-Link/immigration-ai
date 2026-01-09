"""
Audit log model for rule parsing operations.

Tracks all parsing operations for compliance and debugging.
"""

import uuid
from django.db import models
from django.conf import settings
from data_ingestion.models.document_version import DocumentVersion


class RuleParsingAuditLog(models.Model):
    """
    Audit log for rule parsing operations.
    
    Tracks all parsing attempts, successes, failures, and metadata
    for compliance and operational excellence.
    """
    
    ACTION_CHOICES = [
        ('parse_started', 'Parse Started'),
        ('parse_completed', 'Parse Completed'),
        ('parse_failed', 'Parse Failed'),
        ('rule_created', 'Rule Created'),
        ('validation_task_created', 'Validation Task Created'),
        ('cache_hit', 'Cache Hit'),
        ('cache_miss', 'Cache Miss'),
        ('rate_limit_wait', 'Rate Limit Wait'),
        ('pii_detected', 'PII Detected'),
        ('pii_redacted', 'PII Redacted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True,
        help_text="Document version being processed"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Action performed"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rule_parsing_audit_logs',
        help_text="User who triggered the action (if applicable)"
    )
    
    status = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Status: success, failure, warning"
    )
    
    message = models.TextField(
        null=True,
        blank=True,
        help_text="Human-readable message"
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata (tokens, cost, processing time, etc.)"
    )
    
    error_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="Error type if action failed"
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if action failed"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request (if applicable)"
    )
    
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="User agent of the request (if applicable)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'rule_parsing_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_version', 'action']),
            models.Index(fields=['action', 'status']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['error_type']),
        ]
        verbose_name_plural = 'Rule Parsing Audit Logs'
    
    def __str__(self):
        return f"{self.action} - {self.document_version.id} - {self.status}"
