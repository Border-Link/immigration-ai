import uuid
from django.db import models
from .ai_reasoning_log import AIReasoningLog
from data_ingestion.models.document_version import DocumentVersion


class AICitation(models.Model):
    """
    Source attribution for AI outputs.
    Links AI reasoning to source document versions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    reasoning_log = models.ForeignKey(
        AIReasoningLog,
        on_delete=models.CASCADE,
        related_name='citations',
        db_index=True,
        help_text="The reasoning log this citation belongs to"
    )
    
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='ai_citations',
        db_index=True,
        help_text="The document version cited"
    )
    
    excerpt = models.TextField(
        help_text="The excerpt from the document that was cited"
    )
    
    relevance_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Relevance score for this citation (0.0 to 1.0)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ai_citations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reasoning_log', '-created_at']),
        ]
        verbose_name_plural = 'AI Citations'

    def __str__(self):
        return f"Citation for Reasoning {self.reasoning_log.id}"

