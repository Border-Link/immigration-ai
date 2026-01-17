import uuid
from django.db import models
from django.conf import settings
from .parsed_rule import ParsedRule


class RuleValidationTask(models.Model):
    """
    Human validation tasks for parsed rules.
    Reviewers validate AI-extracted rules before they're promoted to production.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    parsed_rule = models.ForeignKey(
        ParsedRule,
        on_delete=models.CASCADE,
        related_name='validation_tasks',
        db_index=True,
        help_text="The parsed rule being validated"
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rule_validation_tasks',
        db_index=True,
        help_text="Reviewer assigned to validate this rule"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current status of the validation task"
    )
    
    reviewer_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notes from the reviewer"
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the review was completed"
    )
    
    sla_deadline = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="SLA deadline for completing this validation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'rule_validation_tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['parsed_rule', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'sla_deadline']),
        ]
        verbose_name_plural = 'Rule Validation Tasks'

    def __str__(self):
        return f"Validation Task for {self.parsed_rule.visa_code} ({self.status})"

