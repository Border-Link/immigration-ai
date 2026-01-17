"""
Review Status History Model

Tracks all status changes for audit and history purposes.
"""
import uuid
from django.db import models
from django.conf import settings
from .review import Review


class ReviewStatusHistory(models.Model):
    """
    Tracks status changes for reviews.
    Provides complete audit trail of review lifecycle.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='status_history',
        db_index=True,
        help_text="The review this status change belongs to"
    )
    
    previous_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Previous status before change"
    )
    
    new_status = models.CharField(
        max_length=20,
        help_text="New status after change"
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_status_changes',
        help_text="User who made the status change"
    )
    
    reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for the status change"
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata about the status change"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this history entry is soft-deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this history entry was soft-deleted")

    class Meta:
        db_table = 'review_status_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['review', '-created_at']),
            models.Index(fields=['changed_by', '-created_at']),
            models.Index(fields=['new_status', '-created_at']),
        ]
        verbose_name_plural = 'Review Status History'

    def __str__(self):
        return f"Status change for Review {self.review.id}: {self.previous_status} -> {self.new_status}"
