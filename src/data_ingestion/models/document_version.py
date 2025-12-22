import uuid
import hashlib
from django.db import models
from .source_document import SourceDocument


class DocumentVersion(models.Model):
    """
    Versioned extracted text from source documents.
    Each version represents a unique state of the document content.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    source_document = models.ForeignKey(
        SourceDocument,
        on_delete=models.CASCADE,
        related_name='document_versions',
        db_index=True,
        help_text="The source document this version was extracted from"
    )
    
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of the extracted text for change detection"
    )
    
    raw_text = models.TextField(
        help_text="Extracted text content (cleaned HTML, PDF text, etc.)"
    )
    
    extracted_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this version was extracted"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (page numbers, sections, etc.)"
    )

    class Meta:
        db_table = 'document_versions'
        ordering = ['-extracted_at']
        indexes = [
            models.Index(fields=['source_document', '-extracted_at']),
            models.Index(fields=['content_hash']),
        ]
        verbose_name_plural = 'Document Versions'

    def __str__(self):
        return f"Version {self.content_hash[:8]}... ({self.extracted_at})"

