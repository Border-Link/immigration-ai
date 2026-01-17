import uuid
from django.db import models
from .review import Review


class ReviewNote(models.Model):
    """
    Reviewer annotations and reasoning.
    Notes added during the review process.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='notes',
        db_index=True,
        help_text="The review this note belongs to"
    )
    
    note = models.TextField(
        help_text="The note content"
    )
    
    is_internal = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this note is internal (not visible to user)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this note is soft-deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this note was soft-deleted")

    class Meta:
        db_table = 'review_notes'
        ordering = ['-created_at']
        verbose_name_plural = 'Review Notes'

    def __str__(self):
        return f"Note for Review {self.review.id}"

