"""
Case Status History Model

Tracks all status changes for cases for audit and history purposes.
"""
import uuid
from django.db import models
from django.conf import settings
from .case import Case


class CaseStatusHistory(models.Model):
    """
    Tracks status changes for cases.
    Provides complete audit trail of case lifecycle.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='status_history',
        db_index=True,
        help_text="The case whose status changed"
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
        related_name='case_status_changes',
        help_text="The user who initiated the status change"
    )
    
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for the status change"
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata about the status change"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'case_status_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', '-created_at']),
            models.Index(fields=['changed_by', '-created_at']),
            models.Index(fields=['new_status', '-created_at']),
        ]
        verbose_name_plural = 'Case Status History'

    def __str__(self):
        return f"Status change for Case {self.case.id}: {self.previous_status} -> {self.new_status}"
