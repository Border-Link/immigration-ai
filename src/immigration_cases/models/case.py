import uuid
from django.db import models
from django.conf import settings


class Case(models.Model):
    """
    Core entity representing one immigration journey.
    Status workflow: draft → evaluated → awaiting_review → reviewed → closed
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('evaluated', 'Evaluated'),
        ('awaiting_review', 'Awaiting Review'),
        ('reviewed', 'Reviewed'),
        ('closed', 'Closed'),
    ]

    JURISDICTION_CHOICES = [
        ('UK', 'United Kingdom'),
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cases',
        db_index=True,
        help_text="The user who owns this case"
    )
    
    jurisdiction = models.CharField(
        max_length=10,
        choices=JURISDICTION_CHOICES,
        db_index=True,
        help_text="Jurisdiction for this immigration case"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Current status of the case"
    )
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete fields
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this case is soft deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this case was deleted")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['jurisdiction', 'status']),
            models.Index(fields=['is_deleted', '-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=[choice[0] for choice in STATUS_CHOICES]),
                name='valid_case_status'
            ),
        ]
        verbose_name_plural = 'Cases'

    def __str__(self):
        return f"Case {self.id} - {self.user.email} ({self.jurisdiction})"

