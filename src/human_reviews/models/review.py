import uuid
from django.db import models
from django.conf import settings
from immigration_cases.models.case import Case


class Review(models.Model):
    """
    Human review workflow management.
    Tracks reviewer assignments and review status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True,
        help_text="The case being reviewed"
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        db_index=True,
        help_text="The reviewer assigned to this review"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current status of the review"
    )
    
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the review was assigned"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the review was completed"
    )
    
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this review is soft-deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this review was soft-deleted")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['reviewer', 'status']),
        ]
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f"Review {self.id} - Case {self.case.id} ({self.status})"

