"""
Processing History model for tracking document processing operations.
"""
import uuid
from django.db import models
from django.conf import settings
from document_handling.models.case_document import CaseDocument


class ProcessingHistory(models.Model):
    """
    Audit log for document processing operations.
    
    Tracks all processing attempts, successes, failures, and metadata
    for compliance and operational excellence.
    """
    
    ACTION_CHOICES = [
        ('ocr_started', 'OCR Started'),
        ('ocr_completed', 'OCR Completed'),
        ('ocr_failed', 'OCR Failed'),
        ('classification_started', 'Classification Started'),
        ('classification_completed', 'Classification Completed'),
        ('classification_failed', 'Classification Failed'),
        ('validation_started', 'Validation Started'),
        ('validation_completed', 'Validation Completed'),
        ('validation_failed', 'Validation Failed'),
        ('job_created', 'Job Created'),
        ('job_queued', 'Job Queued'),
        ('job_started', 'Job Started'),
        ('job_completed', 'Job Completed'),
        ('job_failed', 'Job Failed'),
        ('job_cancelled', 'Job Cancelled'),
        ('retry_attempted', 'Retry Attempted'),
        ('manual_override', 'Manual Override'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case_document = models.ForeignKey(
        CaseDocument,
        on_delete=models.CASCADE,
        related_name='processing_history',
        db_index=True,
        help_text="Document being processed"
    )
    
    processing_job = models.ForeignKey(
        'ProcessingJob',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_entries',
        db_index=True,
        help_text="Processing job this history entry belongs to"
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
        related_name='processing_history_entries',
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
        help_text="Additional metadata (processing time, tokens, cost, confidence, etc.)"
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
    
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Processing time in milliseconds"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this history entry is soft-deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this history entry was soft-deleted")

    class Meta:
        db_table = 'processing_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case_document', 'action']),
            models.Index(fields=['processing_job', 'action']),
            models.Index(fields=['action', 'status']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['error_type']),
        ]
        verbose_name_plural = 'Processing History'

    def __str__(self):
        return f"{self.action} - {self.case_document.id} - {self.status}"
