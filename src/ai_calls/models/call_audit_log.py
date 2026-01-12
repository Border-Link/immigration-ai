import uuid
from django.db import models


class CallAuditLog(models.Model):
    """
    Compliance audit log for call events.
    Tracks guardrails triggers, refusals, warnings, escalations.
    """
    EVENT_TYPE_CHOICES = [
        ('guardrail_triggered', 'Guardrail Triggered'),
        ('refusal', 'Refusal'),
        ('warning', 'Warning'),
        ('escalation', 'Escalation'),
        ('timebox_warning', 'Timebox Warning'),
        ('auto_termination', 'Auto Termination'),
        ('manual_termination', 'Manual Termination'),
        ('state_transition', 'State Transition'),
        ('invalid_transition_attempt', 'Invalid Transition Attempt'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    call_session = models.ForeignKey(
        'ai_calls.CallSession',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True,
        help_text="The call session this audit log belongs to"
    )
    
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of audit event"
    )
    
    description = models.TextField(help_text="Description of the event")
    
    # Context
    user_input = models.TextField(
        null=True,
        blank=True,
        help_text="User input that triggered the event (if applicable)"
    )
    
    ai_response = models.TextField(
        null=True,
        blank=True,
        help_text="AI response (if applicable)"
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata about the event"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'call_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['call_session', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f"CallAuditLog {self.event_type} - {self.call_session.id}"
