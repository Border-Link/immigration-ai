import uuid
from django.db import models
from .data_source import DataSource


class SourceDocument(models.Model):
    """
    Raw fetched content from a data source (immutable).
    Represents a single fetch operation from a source.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='source_documents',
        db_index=True,
        help_text="The data source this document was fetched from"
    )
    
    source_url = models.URLField(
        max_length=1000,
        db_index=True,
        help_text="Full URL of the fetched document"
    )
    
    fetched_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this document was fetched"
    )
    
    raw_content = models.TextField(
        help_text="Raw content as fetched (HTML, JSON, PDF text, etc.)"
    )
    
    content_type = models.CharField(
        max_length=100,
        default='text/html',
        help_text="Content type (text/html, application/json, application/pdf, etc.)"
    )
    
    http_status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code from the fetch operation"
    )
    
    fetch_error = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if fetch failed"
    )

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'source_documents'
        ordering = ['-fetched_at']
        indexes = [
            models.Index(fields=['data_source', '-fetched_at']),
            models.Index(fields=['source_url']),
        ]
        verbose_name_plural = 'Source Documents'

    def __str__(self):
        return f"{self.source_url} ({self.fetched_at})"

