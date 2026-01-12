# One-on-One AI Immigration Case Call — Service Design

**Version:** 2.0  
**Date:** 2025  
**Status:** Enterprise-Ready Implementation Plan  
**Author:** Lead Principal Engineer  
**Last Updated:** 2025-01-XX

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Core Design Principles](#3-core-design-principles)
4. [State Machine & Enforced Transitions](#4-state-machine--enforced-transitions)
5. [Data Models](#5-data-models)
6. [Service Layer Design](#6-service-layer-design)
7. [API Specification](#7-api-specification)
8. [Integration Points](#8-integration-points)
9. [Security & Compliance](#9-security--compliance)
10. [Enterprise Failure Modes](#10-enterprise-failure-modes)
11. [Non-Goals & Compliance Boundaries](#11-non-goals--compliance-boundaries)
12. [Implementation Plan](#12-implementation-plan)
13. [Directory Structure](#13-directory-structure)
14. [Key Implementation Details](#14-key-implementation-details)
15. [Testing Strategy](#15-testing-strategy)
16. [Monitoring & Observability](#16-monitoring--observability)
17. [Future Enhancements](#17-future-enhancements)
18. [Compliance Notes](#18-compliance-notes)

---

## 1. Executive Summary

### 1.1 Service Purpose

The AI Call Service enables applicants to have a **30-minute, case-scoped, voice-based conversation** with an AI agent about their specific immigration case. Unlike generic interview AIs, this service:

- **Case-Scoped**: AI can only discuss the assigned immigration case
- **Time-Bounded**: Exactly 30 minutes per call (hard stop)
- **Context-Aware**: Pre-loaded with case facts, documents, reviews, rules, and AI decisions
- **Auditable**: Full transcript and interaction logging
- **Compliance-Friendly**: Clear guardrails, no legal advice drift

### 1.2 Value Proposition

**For Users (Applicants)**:
- Real-time voice interaction for complex questions
- Case-specific guidance without generic responses
- Immediate answers to eligibility, document, and timeline questions
- Post-call summary automatically attached to case timeline

**For Business**:
- Differentiated offering vs. generic interview AIs
- Native integration with case management system
- Full audit trail for compliance
- Scalable voice infrastructure

### 1.3 Key Differentiators

| Generic Interview AI | AI Call Service |
|---------------------|-----------------|
| Generic interview | Case-specific reasoning |
| External meeting tool (Google Meet, Zoom) | Native, controlled environment |
| Broad questioning | Strictly scoped to immigration case |
| No persistent context | Case timeline integration |
| Hard to audit | Fully logged & reviewable |
| Proactive AI guidance | Reactive-only (user-driven) |
| No state machine enforcement | Strict state machine with validation |
| Single-layer guardrails | Dual-layer (pre-prompt + post-response) |
| Traffic-dependent timebox | Independent background scheduler |

### 1.4 Architectural Decisions

**Why NOT Google Meet / External Meeting Tools**:
- **Compliance Risk**: External tools cannot enforce our strict guardrails
- **Audit Trail Gaps**: Cannot guarantee full transcript capture or context sealing
- **No State Machine Control**: External tools don't respect our enforced state transitions
- **Data Sovereignty**: Call data would flow through third-party infrastructure
- **Integration Complexity**: Cannot integrate with case timeline or context bundle
- **Cost Control**: External tools charge per-minute, no fixed pricing model
- **Custom Guardrails**: Cannot implement dual-layer validation or reactive-only model

**Why Native WebRTC / Managed Voice Provider**:
- Full control over call lifecycle and state machine
- Complete audit trail and transcript capture
- Native integration with case context and guardrails
- Predictable pricing and cost control
- Compliance-friendly data handling

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
User (Web/Mobile App)
 └── Call Session API
       ├── Case Context Builder
       ├── AI Voice Orchestrator
       ├── Timebox & Guardrails Engine
       ├── Audit Logger
       └── Post-Call Summary Generator
```

### 2.2 Service Integration

```
ai_calls/
├── models/
│   ├── call_session.py          # Core call session entity
│   ├── call_transcript.py       # Turn-by-turn transcript
│   ├── call_audit_log.py        # Compliance audit trail
│   └── call_summary.py          # Post-call summary
├── services/
│   ├── call_session_service.py  # Core orchestrator
│   ├── case_context_builder.py   # Context preparation
│   ├── voice_orchestrator.py     # Speech-to-text/text-to-speech
│   ├── timebox_service.py        # 30-minute enforcement
│   ├── guardrails_service.py     # Scope & compliance checks
│   └── post_call_summary_service.py  # Summary generation
├── repositories/
│   ├── call_session_repository.py
│   ├── call_transcript_repository.py
│   └── call_audit_log_repository.py
├── selectors/
│   ├── call_session_selector.py
│   ├── call_transcript_selector.py
│   └── call_audit_log_selector.py
├── serializers/
│   ├── call_session/
│   │   ├── create.py
│   │   ├── read.py
│   │   └── update.py
│   └── call_transcript/
│       └── read.py
├── views/
│   ├── call_session/
│   │   ├── create.py
│   │   ├── read.py
│   │   ├── update.py
│   │   └── terminate.py
│   └── admin/
│       ├── call_session_admin.py
│       └── call_analytics.py
├── helpers/
│   ├── context_builder.py
│   ├── guardrails_validator.py
│   └── voice_utils.py
└── urls.py
```

### 2.3 Layer Responsibilities

**Views Layer** (`views/`):
- Handle HTTP requests/responses
- Validate input via serializers
- Call services only (no direct model access)
- Return serialized responses
- Admin views separated in `views/admin/`

**Services Layer** (`services/`):
- Business logic orchestration
- Call selectors (read) and repositories (write)
- No direct ORM access
- Audit logging integration
- Context building, guardrails, timebox enforcement

**Selectors Layer** (`selectors/`):
- Read-only database operations
- Optimized queries with `select_related`
- Advanced filtering for admin
- Caching support

**Repositories Layer** (`repositories/`):
- Write-only database operations
- Transaction management with `transaction.atomic()`
- Optimistic locking support
- Proper validation

---

## 3. Core Design Principles

### 3.1 Case Scoping

**Rule**: AI can only discuss the assigned immigration case.

**Implementation**:
- Call session is created with a specific `case_id`
- Case context is pre-built and sealed before call starts
- AI cannot query database live during call
- Guardrails service validates each AI response against case scope

**Context Bundle Structure**:
```json
{
  "case_id": "uuid",
  "case_type": "StudentVisa",
  "allowed_topics": [
    "eligibility",
    "documents",
    "timeline",
    "next_steps"
  ],
  "documents_summary": "...",
  "human_review_notes": "...",
  "ai_findings": "...",
  "rules_knowledge": "...",
  "restricted_topics": [
    "other visas",
    "legal guarantees",
    "case outcomes"
  ]
}
```

### 3.2 Time Bounding

**Rule**: Exactly 30 minutes per call (hard stop).

**Implementation**:
- `CallSession` model tracks `started_at` and `duration_seconds`
- `TimeboxService` enforces 30-minute limit
- Warnings at 5 minutes and 1 minute remaining
- Auto-termination at 30 minutes (no extension, no resume)

### 3.3 Context Awareness

**Rule**: AI must have full case context before call starts.

**Implementation**:
- `CaseContextBuilder` assembles context bundle
- Includes: case facts, documents, reviews, AI decisions, applicable rules
- Context is read-only and sealed
- No live database queries during call

### 3.4 Auditability

**Rule**: Every interaction must be logged.

**Implementation**:
- `CallTranscript` model stores turn-by-turn transcript
- `CallAuditLog` stores compliance events (refusals, warnings, terminations)
- Full timestamp tracking
- Integration with `AuditLogService` for system-wide audit trail

### 3.5 Compliance

**Rule**: Clear guardrails, no legal advice drift.

**Implementation**:
- `GuardrailsService` validates AI responses
- Safety language enforcement ("Based on your case information...")
- Refusal templates for off-scope questions
- Escalation to human review when guardrails triggered

### 3.6 Reactive-Only Conversation Model

**Rule**: AI never initiates conversation or leads the user. AI only responds to user questions.

**Implementation**:
- AI waits for user input before generating any response
- No proactive suggestions, prompts, or guidance
- No "Would you like to know about X?" type questions
- AI responds only when user asks a question
- This prevents AI from steering conversation into off-scope territory
- Reduces compliance risk of AI appearing to give unsolicited advice

**Rationale**:
- User-driven conversation ensures compliance boundaries
- Prevents AI from accidentally venturing into legal advice territory
- Reduces guardrails trigger rate
- Aligns with OISC guidance: information provided only when requested

### 3.7 Context Versioning & Deterministic Audits

**Rule**: Context bundle is versioned and hashed for deterministic audit trails.

**Implementation**:
- Context bundle includes `version` and `content_hash` fields
- Hash computed using SHA-256 of canonicalized JSON
- Version increments when context is rebuilt (case updated)
- Audit logs reference context version and hash
- Enables deterministic replay of AI responses for compliance review
- Prevents context tampering or drift during call

### 3.8 Prompt Governance

**Rule**: Raw prompts are not stored by default (privacy and security).

**Implementation**:
- `CallTranscript.ai_prompt_used` field is optional and only populated when:
  - Admin explicitly requests prompt storage (for debugging)
  - Guardrails are triggered (for compliance review)
  - Call is escalated (for human review)
- Default behavior: Store prompt hash only, not full prompt
- Prompt reconstruction possible from context bundle + conversation history
- Reduces storage costs and privacy exposure
- Still enables compliance audits when needed

---

## 4. State Machine & Enforced Transitions

### 4.1 State Machine Definition

**Strict State Machine**: All status transitions are enforced programmatically. Invalid transitions raise exceptions and are logged as security events.

**Valid States**:
- `created`: Session created, context not yet built
- `ready`: Context built and sealed, call can start
- `in_progress`: Call is active
- `completed`: Call ended normally (30 minutes or user ended)
- `expired`: Call session expired before starting (TTL exceeded)
- `terminated`: Call terminated manually (user or admin)

**Valid Transitions**:
```python
VALID_TRANSITIONS = {
    'created': ['ready', 'expired', 'terminated'],
    'ready': ['in_progress', 'expired', 'terminated'],
    'in_progress': ['completed', 'terminated'],
    'completed': [],  # Terminal state
    'expired': [],  # Terminal state
    'terminated': [],  # Terminal state
}
```

### 4.2 State Transition Validator

**Implementation**:
```python
class CallSessionStateValidator:
    """Enforces strict state machine for call sessions."""
    
    VALID_TRANSITIONS = {
        'created': ['ready', 'expired', 'terminated'],
        'ready': ['in_progress', 'expired', 'terminated'],
        'in_progress': ['completed', 'terminated'],
        'completed': [],
        'expired': [],
        'terminated': [],
    }
    
    @staticmethod
    def validate_transition(current_status: str, new_status: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a status transition.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if current_status == new_status:
            return True, None
        
        if current_status not in VALID_TRANSITIONS:
            return False, f"Invalid current status: {current_status}"
        
        if new_status not in VALID_TRANSITIONS:
            return False, f"Invalid new status: {new_status}"
        
        if new_status not in VALID_TRANSITIONS[current_status]:
            return False, (
                f"Invalid transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(VALID_TRANSITIONS[current_status])}"
            )
        
        return True, None
    
    @staticmethod
    def get_valid_transitions(current_status: str) -> List[str]:
        """Get list of valid transitions from current status."""
        return VALID_TRANSITIONS.get(current_status, [])
```

**Enforcement Points**:
- All service methods that update status must call validator
- Repository layer enforces validation before database write
- Invalid transitions raise `InvalidStateTransitionError`
- Security event logged for invalid transition attempts
- Optimistic locking prevents race conditions in state updates

### 4.3 State Transition Examples

**Valid Flow**:
1. `created` → `ready` (context built)
2. `ready` → `in_progress` (call started)
3. `in_progress` → `completed` (call ended normally)

**Invalid Flow** (will raise exception):
1. `created` → `in_progress` (skipping `ready` - INVALID)
2. `completed` → `in_progress` (terminal state - INVALID)
3. `expired` → `ready` (terminal state - INVALID)

**Security Implications**:
- Invalid transitions indicate potential security issue or bug
- All invalid transition attempts are logged to `CallAuditLog`
- Admin alerts triggered if invalid transitions detected in production

---

## 5. Data Models

### 4.1 CallSession Model

```python
class CallSession(models.Model):
    """
    Represents a single AI call session for an immigration case.
    State: CREATED → READY → IN_PROGRESS → COMPLETED → EXPIRED
    """
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('ready', 'Ready'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

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
        related_name='call_session',
        help_text="Post-call summary (generated after call ends)"
    )
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
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
                check=models.Q(status__in=[choice[0] for choice in STATUS_CHOICES]),
                name='valid_call_session_status'
            ),
        ]
```

### 4.2 CallTranscript Model

```python
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
```

### 4.3 CallAuditLog Model

```python
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
```

### 4.4 CallSummary Model

```python
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
        help_text="List of key questions asked during the call"
    )
    
    action_items = models.JSONField(
        default=list,
        help_text="List of action items identified"
    )
    
    missing_documents = models.JSONField(
        default=list,
        help_text="List of missing documents identified"
    )
    
    suggested_next_steps = models.JSONField(
        default=list,
        help_text="List of suggested next steps (non-binding)"
    )
    
    # Statistics
    total_turns = models.IntegerField(help_text="Total number of turns in the call")
    total_duration_seconds = models.IntegerField(help_text="Total call duration in seconds")
    topics_discussed = models.JSONField(
        default=list,
        help_text="List of topics discussed"
    )
    
    # Integration
    attached_to_case = models.BooleanField(
        default=False,
        help_text="Whether summary has been attached to case timeline"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'call_summaries'
        ordering = ['-created_at']
```

---

## 6. Service Layer Design

### 5.1 CallSessionService (Core Orchestrator)

**Responsibilities**:
- Create call session
- Validate case eligibility
- Build case context
- Start/end call
- Terminate call
- Get call status

**Key Methods**:

```python
class CallSessionService:
    @staticmethod
    def create_call_session(case_id: str, user_id: str) -> Optional[CallSession]:
        """
        Create a new call session.
        
        Validates:
        - Case exists and belongs to user
        - Case is in valid state (not closed)
        - User doesn't have active call for this case
        - Case has sufficient context (facts, documents, etc.)
        
        Returns:
        - CallSession in 'created' status
        """
    
    @staticmethod
    def prepare_call_session(session_id: str) -> Optional[CallSession]:
        """
        Prepare call session by building context bundle.
        
        Steps:
        1. Validate current status is 'created' (state machine enforcement)
        2. Build case context (CaseContextBuilder)
        3. Compute context hash (SHA-256)
        4. Seal context bundle (mark as read-only)
        5. Validate transition 'created' → 'ready'
        6. Update status to 'ready' with optimistic locking
        
        Returns:
        - CallSession in 'ready' status
        """
    
    @staticmethod
    def start_call(session_id: str) -> Optional[CallSession]:
        """
        Start the call.
        
        Steps:
        1. Validate session is 'ready' (state machine check)
        2. Validate transition 'ready' → 'in_progress'
        3. Initialize WebRTC session
        4. Schedule timebox enforcement task (background scheduler)
        5. Update status to 'in_progress' with optimistic locking
        6. Record started_at timestamp
        
        Returns:
        - CallSession in 'in_progress' status
        """
    
    @staticmethod
    def end_call(session_id: str, reason: str = 'completed') -> Optional[CallSession]:
        """
        End the call normally.
        
        Steps:
        1. Validate session is 'in_progress' (state machine check)
        2. Validate transition 'in_progress' → 'completed'
        3. Cancel timebox enforcement task
        4. Generate post-call summary
        5. Attach summary to case timeline
        6. Update status to 'completed' with optimistic locking
        7. Record ended_at and duration_seconds
        
        Returns:
        - CallSession in 'completed' status
        """
    
    @staticmethod
    def terminate_call(session_id: str, reason: str, terminated_by_user_id: str) -> Optional[CallSession]:
        """
        Manually terminate call (user or admin).
        
        Steps:
        1. Stop timebox timer
        2. Generate partial summary (if call had content)
        3. Update status to 'terminated'
        4. Log termination in audit log
        
        Returns:
        - CallSession in 'terminated' status
        """
    
    @staticmethod
    @cache_result(timeout=300, keys=['session_id'])
    def get_call_session(session_id: str) -> Optional[CallSession]:
        """Get call session by ID."""
    
    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])
    def get_active_call_for_case(case_id: str) -> Optional[CallSession]:
        """Get active call session for a case (if exists)."""
```

### 5.2 CaseContextBuilder (Critical Component)

**Responsibilities**:
- Assemble case context bundle
- Include all relevant case information
- Seal context (read-only)
- Define allowed/restricted topics

**Key Methods**:

```python
class CaseContextBuilder:
    @staticmethod
    def build_context_bundle(case_id: str, version: int = None) -> Dict[str, Any]:
        """
        Build comprehensive case context bundle with versioning.
        
        Includes:
        - Case metadata (type, status, jurisdiction)
        - Case facts (all facts from CaseFact model)
        - Documents summary (uploaded documents, status)
        - Human review notes (if any)
        - AI decisions (eligibility results, confidence scores)
        - Applicable rules (visa requirements, document requirements)
        - Outstanding issues/flags
        - Version and timestamp for deterministic audits
        
        Returns:
        - Sealed context bundle (dict) with version and hash
        """
    
    @staticmethod
    def compute_context_hash(context_bundle: Dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of context bundle for deterministic audits.
        
        Uses canonicalized JSON (sorted keys, no whitespace).
        """
    
    @staticmethod
    def get_allowed_topics(case: Case) -> List[str]:
        """Get list of allowed topics for this case."""
    
    @staticmethod
    def get_restricted_topics() -> List[str]:
        """Get list of always-restricted topics."""
```

### 5.3 VoiceOrchestrator

**Responsibilities**:
- Handle speech-to-text (user voice → text)
- Handle text-to-speech (AI text → voice)
- Manage turn-taking
- Handle interruptions

**Key Methods**:

```python
class VoiceOrchestrator:
    @staticmethod
    def process_user_speech(audio_data: bytes, session_id: str) -> Dict[str, Any]:
        """
        Process user speech input.
        
        Steps:
        1. Convert audio to text (speech-to-text service)
        2. Validate text quality
        3. Create CallTranscript entry (user turn)
        4. Return transcribed text
        
        Returns:
        - Dict with 'text', 'confidence', 'turn_id'
        """
    
    @staticmethod
    def generate_ai_response(user_text: str, session_id: str, store_prompt: bool = False) -> Dict[str, Any]:
        """
        Generate AI response to user input (REACTIVE-ONLY).
        
        IMPORTANT: AI never initiates conversation. This method is only called
        in response to user input.
        
        Steps:
        1. Pre-prompt guardrails: Validate user input against case scope
        2. Build AI prompt with context bundle (includes reactive-only instructions)
        3. Compute prompt hash (for audit trail)
        4. Call LLM API
        5. Post-response guardrails: Validate AI response for compliance
        6. Apply safety language if needed
        7. Create CallTranscript entry (AI turn)
           - Store prompt hash by default
           - Store full prompt only if store_prompt=True or guardrails triggered
        8. Convert text to speech
        9. Return audio + text
        
        Returns:
        - Dict with 'text', 'audio', 'turn_id', 'guardrails_triggered', 'prompt_hash'
        """
    
    @staticmethod
    def handle_interruption(session_id: str):
        """Handle user interruption during AI response."""
```

### 5.4 TimeboxService (Independent Background Scheduler)

**Responsibilities**:
- Enforce 30-minute limit independently (not traffic-dependent)
- Provide warnings at 5 minutes and 1 minute
- Auto-terminate at limit via background scheduler
- Handle network drops and silence gracefully

**Key Methods**:

```python
class TimeboxService:
    @staticmethod
    def schedule_timebox_enforcement(session_id: str, started_at: datetime) -> str:
        """
        Schedule background task to enforce timebox.
        
        Creates Celery task scheduled for 30 minutes from started_at.
        Task runs independently of API traffic.
        
        Returns:
        - Task ID for cancellation if needed
        """
    
    @staticmethod
    def cancel_timebox_enforcement(task_id: str) -> bool:
        """Cancel scheduled timebox enforcement task."""
    
    @staticmethod
    def check_time_remaining(session_id: str) -> Dict[str, Any]:
        """
        Check remaining time for call.
        
        Returns:
        - Dict with 'remaining_seconds', 'warning_level' (none/5min/1min)
        """
    
    @staticmethod
    def should_warn(session_id: str) -> bool:
        """Check if warning should be shown (5 min or 1 min remaining)."""
    
    @staticmethod
    def should_terminate(session_id: str) -> bool:
        """Check if call should be auto-terminated (30 minutes reached)."""
    
    @staticmethod
    def enforce_timebox(session_id: str) -> Optional[CallSession]:
        """
        Background task: Enforce 30-minute timebox.
        
        Called by Celery scheduler at 30-minute mark.
        Independent of API traffic - ensures timebox is enforced even if
        user stops making requests.
        
        Steps:
        1. Check if call is still 'in_progress'
        2. Check if 30 minutes have elapsed
        3. If yes, auto-terminate call
        4. Generate partial summary
        5. Log termination in audit log
        """
    
    @staticmethod
    def send_warning(session_id: str, warning_level: str) -> bool:
        """
        Send timebox warning (5 min or 1 min remaining).
        
        Called by background scheduler, not dependent on user requests.
        """
```

### 5.5 GuardrailsService (Dual-Layer Validation)

**Responsibilities**:
- **Pre-prompt validation**: Validate user questions before sending to AI
- **Post-response validation**: Validate AI responses before returning to user
- Trigger refusals/warnings/escalations
- Enforce reactive-only conversation model

**Dual-Layer Architecture**:
1. **Pre-Prompt Layer**: Validates user input before AI sees it
   - Prevents off-scope questions from reaching AI
   - Reduces AI confusion and guardrails triggers
   - Faster response (no AI call needed for refusals)
   
2. **Post-Response Layer**: Validates AI output before user sees it
   - Catches AI drift or compliance violations
   - Ensures safety language is present
   - Prevents legal advice language

**Key Methods**:

```python
class GuardrailsService:
    @staticmethod
    def validate_user_input_pre_prompt(user_text: str, context_bundle: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        PRE-PROMPT VALIDATION: Validate user input before sending to AI.
        
        Checks:
        - Is question within case scope?
        - Does question request legal advice?
        - Does question request guarantees?
        - Is question attempting to discuss other cases/visas?
        
        Returns:
        - Tuple of (is_valid, error_message, action)
        - Actions: 'allow', 'refuse', 'warn', 'escalate'
        
        If 'refuse': Return refusal message immediately (no AI call)
        If 'warn': Allow but log warning
        If 'escalate': Allow but flag for human review
        """
    
    @staticmethod
    def validate_ai_response_post_response(ai_text: str, context_bundle: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        POST-RESPONSE VALIDATION: Validate AI output before returning to user.
        
        Checks:
        - No legal advice language
        - Stays within case scope
        - Uses safety language ("Based on your case information...")
        - No guarantees or promises
        - No proactive suggestions (reactive-only enforcement)
        
        Returns:
        - Tuple of (is_valid, error_message, action)
        - If invalid: Response is sanitized or replaced with safe message
        """
    
    @staticmethod
    def enforce_reactive_only(ai_text: str) -> bool:
        """
        Check if AI response violates reactive-only model.
        
        Detects:
        - Proactive questions ("Would you like to know about X?")
        - Unsolicited suggestions
        - AI-initiated topics
        
        Returns:
        - True if reactive-only is violated
        """
    
    @staticmethod
    def generate_refusal_message(off_scope_topic: str) -> str:
        """Generate polite refusal message for off-scope questions."""
    
    @staticmethod
    def generate_safety_language() -> str:
        """Generate safety language prefix for AI responses."""
    
    @staticmethod
    def sanitize_ai_response(ai_text: str, violations: List[str]) -> str:
        """
        Sanitize AI response that failed post-response validation.
        
        Replaces unsafe content with compliant message.
        """
```

### 5.6 PostCallSummaryService

**Responsibilities**:
- Generate post-call summary
- Extract key questions, action items, missing documents
- Attach summary to case timeline

**Key Methods**:

```python
class PostCallSummaryService:
    @staticmethod
    def generate_summary(session_id: str) -> Optional[CallSummary]:
        """
        Generate post-call summary.
        
        Steps:
        1. Analyze full transcript
        2. Extract key questions
        3. Identify action items
        4. Identify missing documents
        5. Suggest next steps
        6. Create CallSummary model
        7. Attach to case timeline (via CaseService)
        
        Returns:
        - CallSummary instance
        """
    
    @staticmethod
    def attach_to_case_timeline(summary_id: str, case_id: str) -> bool:
        """Attach summary to case timeline (creates case note or status history entry)."""
```

### 5.7 TranscriptStorageService (Hot vs Cold Storage)

**Responsibilities**:
- Manage transcript storage tiers
- Archive old transcripts to cold storage
- Optimize query performance for recent transcripts

**Storage Strategy**:
- **Hot Storage**: Recent transcripts (< 90 days), frequently accessed
  - Stored in primary database
  - Fast queries, full text search
  - Used for active case review
  
- **Cold Storage**: Archived transcripts (> 90 days), rarely accessed
  - Stored in object storage (S3) or archive database
  - Slower queries, but lower cost
  - Used for compliance audits and historical analysis

**Key Methods**:

```python
class TranscriptStorageService:
    @staticmethod
    def archive_old_transcripts(days_threshold: int = 90) -> int:
        """
        Archive transcripts older than threshold to cold storage.
        
        Background task runs daily.
        Moves transcripts from hot to cold storage.
        Updates storage_tier and archived_at fields.
        """
    
    @staticmethod
    def get_transcript(session_id: str, include_cold: bool = False) -> List[CallTranscript]:
        """
        Get transcript for session.
        
        By default, only returns hot storage transcripts.
        If include_cold=True, also fetches from cold storage.
        """
```

---

## 7. API Specification

### 6.1 Create Call Session

**Endpoint**: `POST /api/v1/ai-calls/sessions/`

**Request**:
```json
{
  "case_id": "uuid"
}
```

**Response** (201 Created):
```json
{
  "message": "Call session created successfully",
  "data": {
    "id": "uuid",
    "case_id": "uuid",
    "status": "created",
    "created_at": "2025-01-01T10:00:00Z"
  }
}
```

**Errors**:
- 400: Case not found or invalid
- 400: Case already has active call
- 400: Case is closed
- 400: Case has insufficient context

### 6.2 Prepare Call Session

**Endpoint**: `POST /api/v1/ai-calls/sessions/{session_id}/prepare/`

**Response** (200 OK):
```json
{
  "message": "Call session prepared successfully",
  "data": {
    "id": "uuid",
    "status": "ready",
    "ready_at": "2025-01-01T10:01:00Z"
  }
}
```

**Errors**:
- 404: Session not found
- 400: Session not in 'created' status
- 500: Context building failed

### 6.3 Start Call

**Endpoint**: `POST /api/v1/ai-calls/sessions/{session_id}/start/`

**Response** (200 OK):
```json
{
  "message": "Call started successfully",
  "data": {
    "id": "uuid",
    "status": "in_progress",
    "started_at": "2025-01-01T10:02:00Z",
    "webrtc_session_id": "session_123",
    "time_remaining_seconds": 1800
  }
}
```

**Errors**:
- 404: Session not found
- 400: Session not in 'ready' status
- 500: WebRTC initialization failed

### 6.4 Process User Speech

**Endpoint**: `POST /api/v1/ai-calls/sessions/{session_id}/speech/`

**Request** (multipart/form-data):
```
audio: <binary audio data>
```

**Response** (200 OK):
```json
{
  "message": "Speech processed successfully",
  "data": {
    "text": "What documents do I need?",
    "confidence": 0.95,
    "turn_id": "uuid",
    "ai_response": {
      "text": "Based on your case information...",
      "audio_url": "https://...",
      "turn_id": "uuid"
    },
    "time_remaining_seconds": 1750,
    "warning_level": null
  }
}
```

**Errors**:
- 404: Session not found
- 400: Session not in 'in_progress' status
- 400: Speech recognition failed
- 400: Guardrails triggered (refusal)

### 6.5 Get Call Status

**Endpoint**: `GET /api/v1/ai-calls/sessions/{session_id}/`

**Response** (200 OK):
```json
{
  "message": "Call session retrieved successfully",
  "data": {
    "id": "uuid",
    "case_id": "uuid",
    "status": "in_progress",
    "started_at": "2025-01-01T10:02:00Z",
    "time_remaining_seconds": 1750,
    "warnings_count": 0,
    "refusals_count": 0
  }
}
```

### 6.6 End Call

**Endpoint**: `POST /api/v1/ai-calls/sessions/{session_id}/end/`

**Response** (200 OK):
```json
{
  "message": "Call ended successfully",
  "data": {
    "id": "uuid",
    "status": "completed",
    "ended_at": "2025-01-01T10:32:00Z",
    "duration_seconds": 1800,
    "summary": {
      "id": "uuid",
      "summary_text": "...",
      "key_questions": [...],
      "action_items": [...]
    }
  }
}
```

### 6.7 Terminate Call

**Endpoint**: `POST /api/v1/ai-calls/sessions/{session_id}/terminate/`

**Request**:
```json
{
  "reason": "User requested termination"
}
```

**Response** (200 OK):
```json
{
  "message": "Call terminated successfully",
  "data": {
    "id": "uuid",
    "status": "terminated",
    "ended_at": "2025-01-01T10:15:00Z"
  }
}
```

### 6.8 Get Transcript

**Endpoint**: `GET /api/v1/ai-calls/sessions/{session_id}/transcript/`

**Response** (200 OK):
```json
{
  "message": "Transcript retrieved successfully",
  "data": {
    "turns": [
      {
        "turn_number": 1,
        "turn_type": "user",
        "text": "What documents do I need?",
        "timestamp": "2025-01-01T10:02:05Z"
      },
      {
        "turn_number": 2,
        "turn_type": "ai",
        "text": "Based on your case information...",
        "timestamp": "2025-01-01T10:02:08Z"
      }
    ],
    "total_turns": 2
  }
}
```

---

## 8. Integration Points

### 7.1 Integration with Immigration Cases

**Case Context Building**:
- Uses `CaseSelector.get_by_id()` to load case
- Uses `CaseFactSelector.get_by_case()` to load facts
- Uses `CaseDocumentSelector.get_by_case()` to load documents
- Uses `ReviewSelector.get_by_case()` to load review notes
- Uses `EligibilityResultSelector.get_by_case()` to load AI decisions

**Post-Call Summary Attachment**:
- Creates case note or status history entry
- Uses `CaseService.update_case()` to add summary to case timeline

### 7.2 Integration with AI Decisions

**Context Building**:
- Uses `EligibilityResultService.get_by_case()` to get eligibility results
- Uses `AIReasoningLogService.get_by_case()` to get AI reasoning
- Uses `AICitationService.get_by_reasoning_log()` to get citations

**AI Response Generation**:
- Uses `AIReasoningService.run_ai_reasoning()` for RAG-based responses
- Uses case context bundle instead of live database queries

### 7.3 Integration with Rules Knowledge

**Context Building**:
- Uses `VisaRuleVersionService.get_current_by_visa_type()` to get active rules
- Uses `VisaRequirementService.get_by_rule_version()` to get requirements
- Uses `VisaDocumentRequirementService.get_by_rule_version()` to get document requirements

### 7.4 Integration with Audit Logging

**All Operations**:
- Uses `AuditLogService.create_audit_log()` for system-wide audit trail
- Creates `CallAuditLog` entries for call-specific events

---

## 9. Security & Compliance

### 8.1 Authentication & Authorization

- All endpoints require authentication (`AuthAPI` base class)
- Users can only create calls for their own cases
- Admin endpoints require `IsAdminOrStaff` permission

### 8.2 Data Privacy

- Call transcripts encrypted at rest
- Audio data not stored (only transcripts)
- GDPR-compliant: right to erasure for call data
- Soft delete for call sessions

### 8.3 Compliance Guardrails

- No legal advice language
- Safety language in all AI responses
- Refusal templates for off-scope questions
- Full audit trail for compliance review

### 8.4 Rate Limiting

- Max 1 active call per case at a time
- Max 3 calls per case per day
- Max 10 calls per user per day

---

## 10. Enterprise Failure Modes

### 10.1 Network Drops

**Scenario**: User's network connection drops during call.

**Handling**:
- WebRTC connection monitoring detects drop
- Call session remains in `in_progress` state
- Timebox enforcement continues (independent scheduler)
- If connection restored within 5 minutes:
  - Resume call from same session
  - Continue from last transcript turn
- If connection not restored within 5 minutes:
  - Auto-terminate call after 5 minutes of silence
  - Generate partial summary
  - Status: `terminated` (reason: "network_drop")

**Implementation**:
- WebRTC connection state monitoring
- Heartbeat mechanism (ping every 30 seconds)
- Graceful timeout handling

### 10.2 User Silence / No Input

**Scenario**: User doesn't provide input for extended period.

**Handling**:
- After 2 minutes of silence: System message "Are you still there?"
- After 5 minutes of silence: Auto-terminate call
- Generate partial summary with available content
- Status: `terminated` (reason: "user_silence")

**Implementation**:
- Silence detection in VoiceOrchestrator
- Background task monitors last user turn timestamp
- Auto-termination via TimeboxService

### 10.3 AI Service Failure

**Scenario**: LLM API fails or times out.

**Handling**:
- Retry with exponential backoff (max 3 retries)
- If all retries fail:
  - Return graceful error message to user
  - Log failure in CallAuditLog
  - Allow user to retry question
  - If 3 consecutive AI failures: Escalate to human review
- Call continues (not terminated) unless user chooses to end

**Implementation**:
- Retry logic in VoiceOrchestrator
- Circuit breaker pattern for LLM API
- Fallback to cached responses if available

### 10.4 Speech-to-Text Failure

**Scenario**: Speech recognition service fails or returns low confidence.

**Handling**:
- If confidence < 0.7: Request user to repeat
- If confidence < 0.5: Offer text input alternative
- If 3 consecutive failures: Escalate to text-only mode
- Log failures in CallAuditLog

**Implementation**:
- Confidence threshold validation
- Graceful degradation to text input
- User preference for text-only mode

### 10.5 Context Building Failure

**Scenario**: Case context cannot be built (missing data, service unavailable).

**Handling**:
- Call session cannot transition to `ready` state
- User receives error: "Unable to prepare call. Please try again later."
- Case flagged for admin review
- Retry mechanism: User can retry after case data is updated

**Implementation**:
- Context building validation in CaseContextBuilder
- Partial context fallback (if some data missing)
- Admin alert for context building failures

### 10.6 Timebox Enforcement Failure

**Scenario**: Background scheduler fails to enforce 30-minute limit.

**Handling**:
- Redundant enforcement: API layer also checks time on each request
- If background task fails, API layer catches it
- Alert monitoring system if timebox exceeded
- Emergency termination: Admin can manually terminate

**Implementation**:
- Dual enforcement: Background scheduler + API layer checks
- Monitoring alerts for timebox violations
- Admin override capability

---

## 11. Non-Goals & Compliance Boundaries

### 11.1 Explicit Non-Goals

**What This Service Does NOT Do**:

1. **Legal Advice**: 
   - Does not provide legal advice or legal opinions
   - Does not guarantee application outcomes
   - Does not recommend specific legal strategies
   - **Boundary**: Information only, not advice

2. **Proactive Guidance**:
   - Does not initiate conversation topics
   - Does not suggest questions to ask
   - Does not prompt users about missing documents
   - **Boundary**: Reactive-only, user-driven

3. **Case Modification**:
   - Does not update case facts during call
   - Does not upload documents during call
   - Does not change case status
   - **Boundary**: Read-only case access during call

4. **Multi-Case Discussion**:
   - Does not discuss other user cases
   - Does not compare cases
   - Does not provide general immigration advice
   - **Boundary**: Single case scope only

5. **Real-Time Case Updates**:
   - Does not query database during call
   - Does not reflect case changes made during call
   - **Boundary**: Sealed context bundle only

6. **Call Recording** (Phase 1):
   - Does not store audio recordings
   - Does not provide call replay
   - **Boundary**: Transcripts only, no audio storage

7. **External Meeting Tools**:
   - Does not integrate with Google Meet, Zoom, etc.
   - Does not use third-party call infrastructure
   - **Boundary**: Native WebRTC only

### 11.2 Compliance Boundaries

**OISC Compliance**:
- Clear "Not Legal Advice" disclaimers in all AI responses
- Informational guidance only
- Escalation to human reviewers for complex cases
- Full audit trail for compliance review

**GDPR Compliance**:
- Right to erasure for call data
- Data minimization (prompts not stored by default)
- Encryption at rest
- User consent for data processing

**Accessibility**:
- Support for users with hearing impairments (transcript display)
- Support for users with speech impairments (text input option)
- WCAG 2.1 AA compliance

---

## 12. Implementation Plan

### 12.1 Phase 1: Core Infrastructure (Week 1-2)

**Week 1**:
1. Create models (CallSession, CallTranscript, CallAuditLog, CallSummary)
   - Add context_version, context_hash fields
   - Add prompt_hash, storage_tier fields
   - Add state machine constraints
2. Create migrations
3. Create state machine validator (CallSessionStateValidator)
4. Create repositories and selectors
5. Create serializers
6. Write unit tests for models and state machine

**Week 2**:
1. Implement CallSessionService (create, prepare, start, end, terminate)
   - Enforce state machine transitions
   - Add optimistic locking
2. Implement CaseContextBuilder
   - Add context versioning and hashing
3. Implement dual-layer GuardrailsService
   - Pre-prompt validation
   - Post-response validation
   - Reactive-only enforcement
4. Write unit tests for services and state machine

### 12.2 Phase 2: Voice Integration (Week 3-4)

**Week 3**:
1. Integrate speech-to-text service (Google Speech-to-Text or AWS Transcribe)
2. Integrate text-to-speech service (Google TTS or AWS Polly)
3. Implement VoiceOrchestrator
   - Reactive-only conversation model
   - Prompt governance (hash by default)
   - Dual-layer guardrails integration
4. Write integration tests

**Week 4**:
1. Implement WebRTC or managed voice provider integration
   - Connection monitoring
   - Heartbeat mechanism
   - Network drop handling
2. Implement turn-taking logic
3. Implement interruption handling
4. Implement failure mode handling (silence, network drops)
5. Write end-to-end tests

### 12.3 Phase 3: Timebox & Guardrails (Week 5)

**Week 5**:
1. Implement TimeboxService (independent background scheduler)
   - Celery task scheduling
   - Dual enforcement (background + API layer)
   - Warning system (5 min, 1 min)
   - Auto-termination
2. Complete GuardrailsService implementation
   - Pre-prompt validation
   - Post-response validation
   - Reactive-only enforcement
3. Implement failure mode handling
   - Network drop recovery
   - Silence detection
   - AI service retry logic
4. Write tests (including chaos tests for timebox)

### 12.4 Phase 4: Post-Call & Admin (Week 6)

**Week 6**:
1. Implement PostCallSummaryService
2. Implement summary attachment to case timeline
3. Implement TranscriptStorageService (hot/cold storage)
4. Create admin views (list, detail, analytics)
5. Create admin serializers
6. Write tests

### 12.5 Phase 5: Polish & Production (Week 7-8)

**Week 7**:
1. Add caching to selectors
2. Add comprehensive error handling
3. Add monitoring and logging
4. Performance optimization

**Week 8**:
1. Security review
2. Compliance review
3. Documentation
4. Production deployment

---

## 13. Directory Structure

```
ai_calls/
├── __init__.py
├── admin.py
├── apps.py
├── urls.py
├── models/
│   ├── __init__.py
│   ├── call_session.py
│   ├── call_transcript.py
│   ├── call_audit_log.py
│   └── call_summary.py
├── repositories/
│   ├── __init__.py
│   ├── call_session_repository.py
│   ├── call_transcript_repository.py
│   ├── call_audit_log_repository.py
│   └── call_summary_repository.py
├── selectors/
│   ├── __init__.py
│   ├── call_session_selector.py
│   ├── call_transcript_selector.py
│   ├── call_audit_log_selector.py
│   └── call_summary_selector.py
├── services/
│   ├── __init__.py
│   ├── call_session_service.py
│   ├── case_context_builder.py
│   ├── voice_orchestrator.py
│   ├── timebox_service.py
│   ├── guardrails_service.py
│   └── post_call_summary_service.py
├── serializers/
│   ├── __init__.py
│   ├── call_session/
│   │   ├── __init__.py
│   │   ├── create.py
│   │   ├── read.py
│   │   └── update.py
│   ├── call_transcript/
│   │   ├── __init__.py
│   │   └── read.py
│   └── call_summary/
│       ├── __init__.py
│       └── read.py
├── views/
│   ├── __init__.py
│   ├── call_session/
│   │   ├── __init__.py
│   │   ├── create.py
│   │   ├── read.py
│   │   ├── update.py
│   │   └── terminate.py
│   └── admin/
│       ├── __init__.py
│       ├── call_session_admin.py
│       └── call_analytics.py
├── helpers/
│   ├── __init__.py
│   ├── context_builder.py
│   ├── guardrails_validator.py
│   ├── state_machine_validator.py  # State transition enforcement
│   ├── prompt_governance.py         # Prompt hashing and storage logic
│   └── voice_utils.py
├── signals/
│   ├── __init__.py
│   └── call_session_signals.py
├── tasks/
│   ├── __init__.py
│   ├── timebox_tasks.py              # Background timebox enforcement
│   └── transcript_archive_tasks.py    # Hot/cold storage management
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

---

## 14. Key Implementation Details

### 14.1 Context Bundle Structure (with Versioning)

```python
{
    "version": 1,
    "created_at": "2025-01-01T10:00:00Z",
    "content_hash": "sha256:abc123...",
    
    "case_id": "uuid",
    "case_type": "StudentVisa",
    "jurisdiction": "UK",
    "case_status": "evaluated",
    
    "allowed_topics": [
        "eligibility",
        "documents",
        "timeline",
        "next_steps",
        "requirements"
    ],
    
    "restricted_topics": [
        "other visas",
        "legal guarantees",
        "case outcomes",
        "application approval"
    ],
    
    "case_facts": {
        "age": 25,
        "nationality": "Nigeria",
        "has_sponsor": true,
        "salary": 50000
    },
    
    "documents_summary": {
        "uploaded": ["passport", "degree_certificate"],
        "missing": ["financial_statement", "sponsor_letter"],
        "status": {
            "passport": "verified",
            "degree_certificate": "pending_review"
        }
    },
    
    "human_review_notes": [
        {
            "reviewer": "John Doe",
            "note": "Case looks strong, documents verified",
            "created_at": "2025-01-01T09:00:00Z"
        }
    ],
    
    "ai_findings": {
        "eligibility_result": {
            "outcome": "likely",
            "confidence": 0.85,
            "reasoning": "..."
        },
        "missing_facts": ["dependents_count"],
        "warnings": []
    },
    
    "rules_knowledge": {
        "visa_type": "StudentVisa",
        "requirements": [
            {
                "code": "age_requirement",
                "description": "Must be 18 or older",
                "met": true
            }
        ],
        "document_requirements": [
            {
                "type": "passport",
                "mandatory": true,
                "provided": true
            }
        ]
    },
    
    "outstanding_issues": [
        "Missing financial statement",
        "Sponsor letter not yet uploaded"
    ]
}
```

### 14.2 Dual-Layer Guardrails Examples

**Off-Scope Question (Pre-Prompt Refusal)**:
- User: "Can I switch to a work visa?"
- Pre-Prompt Guardrails: **REFUSE** (off-scope detected)
- **No AI call made** - Immediate refusal response
- AI Response: "I can only discuss information related to your current Student Visa case. For questions about other visa types, please consult a qualified immigration adviser."
- Audit Log: Refusal logged with user input

**Legal Advice Attempt (Pre-Prompt Refusal)**:
- User: "Will my application be approved?"
- Pre-Prompt Guardrails: **REFUSE** (guarantee request detected)
- **No AI call made** - Immediate refusal response
- AI Response: "I cannot provide guarantees about application outcomes. Based on your case information, you appear to meet the requirements, but final decisions are made by immigration authorities."
- Audit Log: Refusal logged

**Safe Question (Pre-Prompt Allow, Post-Response Validate)**:
- User: "What documents do I need?"
- Pre-Prompt Guardrails: **ALLOW**
- AI generates response
- Post-Response Guardrails: **VALIDATE** (checks safety language, scope)
- AI Response: "Based on your case information, you need: [list from context bundle]..."
- Audit Log: No violations

**AI Drift (Post-Response Sanitization)**:
- User: "What documents do I need?"
- Pre-Prompt Guardrails: **ALLOW**
- AI generates response with legal advice language
- Post-Response Guardrails: **SANITIZE** (detects legal advice)
- AI Response replaced with: "Based on your case information, the required documents are: [list]. Please note this is informational guidance only, not legal advice."
- Audit Log: Post-response violation logged, response sanitized

### 14.3 Timebox Warnings (Independent Scheduler)

**5 Minutes Remaining**:
- Background scheduler detects 25 minutes elapsed
- System message sent via WebRTC: "You have 5 minutes remaining in this call."
- Visual indicator: Yellow warning badge
- **Independent of user requests** - scheduler sends warning even if user silent

**1 Minute Remaining**:
- Background scheduler detects 29 minutes elapsed
- System message sent via WebRTC: "You have 1 minute remaining. The call will end automatically."
- Visual indicator: Red warning badge
- **Independent of user requests**

**Auto-Termination**:
- Background scheduler detects 30 minutes elapsed
- System message: "Your 30-minute call has ended. A summary will be available shortly."
- Call status: 'completed' (enforced state machine transition)
- Summary generation triggered
- **Independent of user requests** - termination happens even if user stops making requests

### 14.4 Post-Call Summary Example

```json
{
    "summary_text": "During this 30-minute call, we discussed your Student Visa case. You asked about required documents, timeline expectations, and next steps. Based on your case information, you appear to meet the eligibility requirements. However, you still need to upload your financial statement and sponsor letter.",
    
    "key_questions": [
        "What documents do I need?",
        "How long does the process take?",
        "What are my next steps?"
    ],
    
    "action_items": [
        "Upload financial statement",
        "Upload sponsor letter",
        "Complete dependent information"
    ],
    
    "missing_documents": [
        "financial_statement",
        "sponsor_letter"
    ],
    
    "suggested_next_steps": [
        "Upload missing documents within 7 days",
        "Review eligibility results in case dashboard",
        "Consider requesting human review if you have specific questions"
    ],
    
    "topics_discussed": [
        "documents",
        "timeline",
        "next_steps"
    ]
}
```

### 14.5 State Machine Transition Tests

**Required Test Coverage**:
- All valid transitions succeed
- All invalid transitions raise `InvalidStateTransitionError`
- Optimistic locking prevents race conditions
- Security events logged for invalid transitions
- Terminal states cannot transition

**Example Test**:
```python
def test_invalid_transition_raises_error():
    session = create_call_session(status='completed')
    with pytest.raises(InvalidStateTransitionError):
        CallSessionService.start_call(session.id)  # Terminal state
```

---

## 15. Testing Strategy

### 15.1 Unit Tests

- Model validation tests
- **State machine transition tests** (all valid/invalid transitions)
- Service method tests
- **Dual-layer guardrails tests** (pre-prompt + post-response)
- Context builder tests (versioning, hashing)
- Timebox service tests (independent scheduler)
- Prompt governance tests (hash vs full prompt storage)

### 15.2 Integration Tests

- End-to-end call flow (create → prepare → start → end)
- **State machine enforcement** (invalid transitions blocked)
- Voice processing integration
- Case context building integration
- Post-call summary generation
- **Reactive-only conversation model** (no proactive AI)

### 15.3 Compliance Tests

- Guardrails enforcement (pre-prompt + post-response)
- Refusal message generation
- Safety language enforcement
- Audit log completeness
- **Context versioning and hashing** (deterministic audits)
- **Prompt governance** (privacy compliance)

### 15.4 Chaos Tests

- **Timebox enforcement** (background scheduler failure scenarios)
- Network drop recovery
- AI service failure handling
- Speech-to-text failure handling
- Context building failure handling

---

## 16. Monitoring & Observability

### 16.1 Metrics

- Call creation rate
- Call completion rate
- Average call duration
- **Dual-layer guardrails trigger rate** (pre-prompt vs post-response)
- Auto-termination rate
- Voice processing latency
- **State machine violation rate** (invalid transitions attempted)
- **Timebox enforcement accuracy** (background scheduler vs API layer)
- **Context versioning** (how often contexts are rebuilt)
- **Prompt storage rate** (hash-only vs full prompt)

### 16.2 Alerts

- High guardrails trigger rate (>20%)
- **State machine violations** (invalid transitions - security concern)
- Voice processing failures
- **Timebox enforcement failures** (background scheduler not running)
- **Timebox exceeded** (call running > 30 minutes - critical)
- Context building failures
- **Network drop rate** (high connection failures)
- **AI service failure rate** (LLM API issues)

### 16.3 Logging

- All call events logged to `CallAuditLog`
- **State machine transitions** logged with validation results
- **Invalid transition attempts** logged as security events
- Integration with `AuditLogService` for system-wide audit
- Error logging with full context
- **Context version and hash** logged for deterministic audits

---

## 17. Future Enhancements

### 17.1 Phase 2 Features

- Multi-language support
- Call recording (with user consent and GDPR compliance)
- Call replay functionality
- Advanced analytics dashboard
- **Context bundle versioning UI** (show context changes over time)

### 17.2 Phase 3 Features

- **Note**: Proactive AI suggestions are explicitly NOT included (compliance boundary)
- Real-time document validation during call (read-only, no uploads)
- Integration with payment system for premium calls
- Mobile app support
- **Advanced transcript analytics** (topic extraction, sentiment analysis)

---

## 18. Compliance Notes

### 18.1 OISC Boundaries

- Clear "Not Legal Advice" disclaimers in all AI responses
- Informational guidance only (reactive, not proactive)
- Escalation to human reviewers for complex cases
- Full audit trail for compliance review
- **Dual-layer guardrails** prevent legal advice drift
- **Reactive-only model** prevents unsolicited advice

### 18.2 GDPR Compliance

- Right to erasure for call data
- **Data minimization**: Prompts not stored by default (hash only)
- Encryption at rest
- User consent for call recording (if implemented in Phase 2)
- **Context versioning** enables selective data deletion
- **Transcript archiving** (hot/cold storage) for data lifecycle management

### 18.3 Accessibility

- Support for users with hearing impairments (transcript display)
- Support for users with speech impairments (text input option)
- WCAG 2.1 AA compliance
- **Reactive-only model** benefits users who need time to formulate questions

---

---

## 19. Summary of Enterprise Hardening

This design document incorporates **production-critical hardening** beyond the initial design:

### ✅ Implemented Hardening Features

1. **Strict State Machine**: Enforced programmatically with validation, not just described
2. **Reactive-Only Model**: AI never initiates conversation, prevents compliance drift
3. **Dual-Layer Guardrails**: Pre-prompt + post-response validation for defense in depth
4. **Independent Timebox**: Background scheduler, not traffic-dependent
5. **Context Versioning & Hashing**: Deterministic audits, prevents tampering
6. **Prompt Governance**: Hash by default, full prompt only when needed (privacy)
7. **Transcript Scaling**: Hot/cold storage strategy for cost optimization
8. **Google Meet Rejection**: Explicit architectural justification for native approach
9. **Failure Mode Handling**: Network drops, silence, AI failures, timebox failures
10. **Non-Goals**: Clear compliance boundaries to protect against scope creep

### 🎯 Ready For

- ✅ Hand to senior engineering team
- ✅ Share with compliance / legal
- ✅ Use for security review
- ✅ Foundation for implementation tickets
- ✅ Push back on generic meeting tools
- ✅ Push back on proactive AI features
- ✅ Push back on skipping audit/context sealing

---

**Status**: Enterprise-Ready for Implementation  
**Version**: 2.0  
**Next Steps**: 
1. Review and approve enterprise design
2. Create implementation tickets with state machine tests
3. Set up voice infrastructure (WebRTC or managed provider)
4. Begin Phase 1 implementation with state machine enforcement
5. Schedule compliance review with legal team
