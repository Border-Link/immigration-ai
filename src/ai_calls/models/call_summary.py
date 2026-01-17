import uuid
from django.db import models


class CallSummary(models.Model):
    """
    Post-call summary automatically generated after call ends.
    Attached to the immigration case timeline.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    call_session = models.OneToOneField(
        'ai_calls.CallSession',
        on_delete=models.CASCADE,
        related_name='call_summary',
        db_index=True,
        help_text="The call session this summary belongs to"
    )
    
    # Summary content
    summary_text = models.TextField(help_text="Main summary text")
    
    key_questions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of key questions asked during the call"
    )
    
    action_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of action items identified"
    )
    
    missing_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of missing documents identified"
    )
    
    suggested_next_steps = models.JSONField(
        default=list,
        blank=True,
        help_text="List of suggested next steps (non-binding)"
    )
    
    # Statistics
    total_turns = models.IntegerField(help_text="Total number of turns in the call")
    total_duration_seconds = models.IntegerField(help_text="Total call duration in seconds")
    topics_discussed = models.JSONField(
        default=list,
        blank=True,
        help_text="List of topics discussed"
    )
    
    # Integration
    attached_to_case = models.BooleanField(
        default=False,
        help_text="Whether summary has been attached to case timeline"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete (CRITICAL: preserve auditability)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'call_summaries'
        ordering = ['-created_at']

    def __str__(self):
        return f"CallSummary - {self.call_session.id}"
