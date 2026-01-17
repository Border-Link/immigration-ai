import uuid
from django.db import models
from .case_document import CaseDocument


class DocumentCheck(models.Model):
    """
    Automated and human validation results.
    Stores results of OCR, classification, and validation checks.
    """
    CHECK_TYPE_CHOICES = [
        ('ocr', 'OCR'),
        ('classification', 'Classification'),
        ('validation', 'Validation'),
        ('content_validation', 'Content Validation'),
        ('requirement_match', 'Requirement Match'),
        ('authenticity', 'Authenticity Check'),
    ]

    RESULT_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('pending', 'Pending'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case_document = models.ForeignKey(
        CaseDocument,
        on_delete=models.CASCADE,
        related_name='checks',
        db_index=True,
        help_text="The document this check belongs to"
    )
    
    check_type = models.CharField(
        max_length=50,
        choices=CHECK_TYPE_CHOICES,
        db_index=True,
        help_text="Type of check performed"
    )
    
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        db_index=True,
        help_text="Result of the check"
    )
    
    details = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional details about the check result"
    )
    
    performed_by = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Who/what performed the check (AI, human reviewer, etc.)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this check is soft-deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this check was soft-deleted")

    class Meta:
        db_table = 'document_checks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case_document', 'check_type']),
            models.Index(fields=['result', '-created_at']),
        ]
        verbose_name_plural = 'Document Checks'

    def __str__(self):
        return f"{self.check_type} - {self.result} for Document {self.case_document.id}"

