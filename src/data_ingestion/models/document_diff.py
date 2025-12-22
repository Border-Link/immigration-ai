import uuid
from django.db import models
from .document_version import DocumentVersion


class DocumentDiff(models.Model):
    """
    Change detection and classification between document versions.
    """
    CHANGE_TYPE_CHOICES = [
        ('minor_text', 'Minor Text Change'),
        ('requirement_change', 'Requirement Change'),
        ('fee_change', 'Fee Change'),
        ('processing_time_change', 'Processing Time Change'),
        ('major_update', 'Major Update'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    old_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='diffs_as_old',
        db_index=True,
        help_text="Previous version of the document"
    )
    
    new_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='diffs_as_new',
        db_index=True,
        help_text="New version of the document"
    )
    
    diff_text = models.TextField(
        help_text="Unified diff showing changes between versions"
    )
    
    change_type = models.CharField(
        max_length=50,
        choices=CHANGE_TYPE_CHOICES,
        default='minor_text',
        db_index=True,
        help_text="Classification of the type of change detected"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'document_diffs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['old_version', 'new_version']),
            models.Index(fields=['change_type', '-created_at']),
        ]
        verbose_name_plural = 'Document Diffs'
        unique_together = [['old_version', 'new_version']]

    def __str__(self):
        return f"Diff: {self.change_type} ({self.created_at})"

