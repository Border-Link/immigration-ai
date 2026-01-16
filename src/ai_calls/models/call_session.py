import uuid
import hashlib
import json
from django.db import models
from django.conf import settings
from django.utils import timezone

# Status choices for CallSession
STATUS_CHOICES = [
    ('created', 'Created'),
    ('ready', 'Ready'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('expired', 'Expired'),
    ('terminated', 'Terminated'),
    ('failed', 'Failed'),
]


class CallSession(models.Model):
    """
    Represents a single AI call session for an immigration case.
    State: CREATED → READY → IN_PROGRESS → COMPLETED → EXPIRED
    """
    STATUS_CHOICES = STATUS_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        'immigration_cases.Case',
        on_delete=models.CASCADE,
        related_name='call_sessions',
        db_index=True,
        help_text="The immigration case this call is scoped to"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='call_sessions',
        db_index=True,
        help_text="The user who initiated the call"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        db_index=True,
        help_text="Current status of the call session"
    )
    
    # Time tracking
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ready_at = models.DateTimeField(null=True, blank=True, help_text="When context was built and call became ready")
    started_at = models.DateTimeField(null=True, blank=True, help_text="When call actually started")
    ended_at = models.DateTimeField(null=True, blank=True, help_text="When call ended")
    duration_seconds = models.IntegerField(null=True, blank=True, help_text="Actual call duration in seconds")
    last_heartbeat_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Last time the client sent a heartbeat (liveness tracking)"
    )
    
    # Context (sealed, read-only)
    context_bundle = models.JSONField(
        null=True,
        blank=True,
        help_text="Pre-built case context bundle (sealed before call starts)"
    )
    
    # Context versioning for deterministic audits
    context_version = models.IntegerField(
        default=1,
        help_text="Version number of context bundle (increments when rebuilt)"
    )
    
    context_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="SHA-256 hash of context bundle for deterministic audits"
    )
    
    # Voice infrastructure
    webrtc_session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="WebRTC session identifier"
    )
    
    # Timebox enforcement
    timebox_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Celery task ID for timebox enforcement (for cancellation)"
    )
    
    # Guardrails tracking
    warnings_count = models.IntegerField(default=0, help_text="Number of guardrail warnings")
    refusals_count = models.IntegerField(default=0, help_text="Number of off-scope refusals")
    escalated = models.BooleanField(default=False, help_text="Whether call was escalated to human review")
    
    # Post-call
    summary = models.ForeignKey(
        'ai_calls.CallSummary',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_with_summary',  # Reverse accessor name to avoid clash with CallSummary.call_session
        help_text="Post-call summary (generated after call ends)"
    )
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Retry tracking
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts for this call session (max 3 per case)"
    )
    parent_session = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retry_sessions',
        help_text="Parent session if this is a retry"
    )
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'call_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['webrtc_session_id']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=[choice[0] for choice in STATUS_CHOICES]),
                name='valid_call_session_status'
            ),
        ]

    def __str__(self):
        return f"CallSession {self.id} - {self.case.id} ({self.status})"
    
    def compute_context_hash(self) -> str:
        """Compute SHA-256 hash of context bundle for deterministic audits."""
        if not self.context_bundle:
            return ""
        
        # Canonicalize JSON (sorted keys, no whitespace)
        canonical_json = json.dumps(self.context_bundle, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    def is_expired(self) -> bool:
        """Check if call session has expired (not started within TTL)."""
        if self.status != 'created' and self.status != 'ready':
            return False
        
        # Expire if not started within 1 hour of creation
        if self.status == 'created':
            return (timezone.now() - self.created_at).total_seconds() > 3600
        
        # Expire if not started within 1 hour of ready
        if self.status == 'ready' and self.ready_at:
            return (timezone.now() - self.ready_at).total_seconds() > 3600
        
        return False
