import uuid
import hashlib
from django.db import models


class CallTranscript(models.Model):
    """
    Turn-by-turn transcript of the call.
    Each turn represents one exchange (user → AI or AI → user).
    """
    TURN_TYPE_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    call_session = models.ForeignKey(
        'ai_calls.CallSession',
        on_delete=models.CASCADE,
        related_name='transcript_turns',
        db_index=True,
        help_text="The call session this turn belongs to"
    )
    
    turn_number = models.IntegerField(
        db_index=True,
        help_text="Sequential turn number (1, 2, 3, ...)"
    )
    
    turn_type = models.CharField(
        max_length=10,
        choices=TURN_TYPE_CHOICES,
        db_index=True,
        help_text="Type of turn (user, ai, system)"
    )
    
    # Content
    text = models.TextField(help_text="Transcribed text or AI response")
    
    # Speech-to-text metadata (for user turns)
    speech_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Speech-to-text confidence score (0.0-1.0)"
    )
    
    # AI metadata (for AI turns)
    ai_model = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="AI model used (e.g., 'gpt-4', 'claude-3')"
    )
    
    # Prompt governance: store hash by default, full prompt only when needed
    ai_prompt_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="SHA-256 hash of prompt (stored by default for privacy)"
    )
    
    ai_prompt_used = models.TextField(
        null=True,
        blank=True,
        help_text="Full prompt sent to AI (only stored when guardrails triggered or admin requested)"
    )
    
    # Guardrails metadata
    guardrails_triggered = models.BooleanField(
        default=False,
        help_text="Whether guardrails were triggered for this turn"
    )
    
    guardrails_action = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Guardrails action taken (refused, warned, escalated)"
    )
    
    # Timing
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this turn occurred"
    )
    
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Duration of this turn in seconds"
    )
    
    # Storage tier (for scaling strategy)
    storage_tier = models.CharField(
        max_length=20,
        choices=[('hot', 'Hot'), ('cold', 'Cold')],
        default='hot',
        db_index=True,
        help_text="Storage tier: hot (recent, frequently accessed) or cold (archived)"
    )
    
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When transcript was moved to cold storage"
    )

    class Meta:
        db_table = 'call_transcripts'
        ordering = ['call_session', 'turn_number']
        indexes = [
            models.Index(fields=['call_session', 'turn_number']),
            models.Index(fields=['call_session', 'timestamp']),
        ]
        unique_together = [['call_session', 'turn_number']]

    def __str__(self):
        return f"CallTranscript {self.turn_number} - {self.call_session.id} ({self.turn_type})"
    
    @staticmethod
    def compute_prompt_hash(prompt_text: str) -> str:
        """Compute SHA-256 hash of prompt for audit trail."""
        return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()
