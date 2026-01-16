import uuid
from django.db import models
from immigration_cases.models.case import Case
from rules_knowledge.models.document_type import DocumentType


class CaseDocument(models.Model):
    """
    User-uploaded files for immigration cases.
    Documents are processed through OCR and validation.
    """
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        # Used by async processing pipeline when document requires reviewer/user attention
        ('needs_attention', 'Needs Attention'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True,
        help_text="The case this document belongs to"
    )
    
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name='case_documents',
        db_index=True,
        help_text="The type of document"
    )
    
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the stored file"
    )
    
    file_name = models.CharField(
        max_length=255,
        help_text="Original file name"
    )
    
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    
    mime_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="MIME type of the file"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        db_index=True,
        help_text="Current status of the document"
    )
    
    # OCR and Classification fields
    ocr_text = models.TextField(
        null=True,
        blank=True,
        help_text="Extracted text from OCR processing"
    )
    
    classification_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score for document type classification (0.0 to 1.0)"
    )
    
    # Content extraction fields
    expiry_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Expiry date extracted from document (e.g., passport expiry, visa expiry)"
    )
    
    extracted_metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Extracted metadata from document (names, dates, numbers, etc.)"
    )
    
    # Content validation fields
    content_validation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('warning', 'Warning'),
        ],
        default='pending',
        db_index=True,
        help_text="Status of content validation against case facts"
    )
    
    content_validation_details = models.JSONField(
        null=True,
        blank=True,
        help_text="Details of content validation (matched fields, mismatches, etc.)"
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'case_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['document_type', 'status']),
        ]
        verbose_name_plural = 'Case Documents'

    def __str__(self):
        return f"{self.file_name} - Case {self.case.id}"

