"""
Processing Job model for tracking document processing jobs.
"""
import uuid
from django.db import models
from django.conf import settings
from document_handling.models.case_document import CaseDocument


class ProcessingJob(models.Model):
    """
    Tracks document processing jobs (OCR, classification, validation).
    Similar to how data_ingestion tracks ingestion jobs.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PROCESSING_TYPE_CHOICES = [
        ('ocr', 'OCR'),
        ('classification', 'Classification'),
        ('validation', 'Validation'),
        ('full', 'Full Processing'),
        ('reprocess', 'Reprocess'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case_document = models.ForeignKey(
        CaseDocument,
        on_delete=models.CASCADE,
        related_name='processing_jobs',
        db_index=True,
        help_text="The document being processed"
    )
    
    processing_type = models.CharField(
        max_length=50,
        choices=PROCESSING_TYPE_CHOICES,
        db_index=True,
        help_text="Type of processing to perform"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current status of the processing job"
    )
    
    celery_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Celery task ID for tracking"
    )
    
    priority = models.IntegerField(
        default=5,
        help_text="Job priority (1-10, higher is more urgent)"
    )
    
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if processing failed"
    )
    
    error_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Type of error if processing failed"
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata (processing time, tokens used, cost, etc.)"
    )
    
    # Structured cost tracking
    llm_tokens_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of LLM tokens used"
    )
    
    llm_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="LLM cost in USD"
    )
    
    ocr_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="OCR cost in USD"
    )
    
    total_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        db_index=True,
        help_text="Total processing cost in USD"
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When processing started"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When processing completed"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_processing_jobs',
        help_text="User who created this job (if manual)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this job is soft-deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this job was soft-deleted")

    class Meta:
        db_table = 'processing_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case_document', 'status']),
            models.Index(fields=['status', 'priority', '-created_at']),
            models.Index(fields=['processing_type', 'status']),
            models.Index(fields=['celery_task_id']),
            models.Index(fields=['error_type']),
        ]
        verbose_name_plural = 'Processing Jobs'

    def __str__(self):
        return f"Processing Job {self.id} - {self.case_document.file_name} ({self.status})"
