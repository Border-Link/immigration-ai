import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app notification system for users.
    Stores notifications for case updates, review assignments, eligibility results, etc.
    """
    TYPE_CHOICES = [
        ('case_status_update', 'Case Status Update'),
        ('eligibility_result_ready', 'Eligibility Result Ready'),
        ('document_status', 'Document Status'),
        ('document_failed', 'Document Failed'),
        ('review_assigned', 'Review Assigned'),
        ('review_completed', 'Review Completed'),
        ('rule_change', 'Rule Change'),
        ('missing_documents', 'Missing Documents'),
        ('sla_deadline', 'SLA Deadline'),
        ('rule_validation_task', 'Rule Validation Task'),
        ('payment_status', 'Payment Status'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
        help_text="User who receives this notification"
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        db_index=True,
        help_text="Type of notification"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )
    
    message = models.TextField(
        help_text="Notification message"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True,
        help_text="Priority level"
    )
    
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the user has read this notification"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp when notification was read"
    )
    
    # Optional links to related entities
    related_entity_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="Type of related entity (e.g., 'case', 'review', 'document')"
    )
    
    related_entity_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID of related entity"
    )
    
    # Metadata for additional context
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata (JSON)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['related_entity_type', 'related_entity_id']),
        ]
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

