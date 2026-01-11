# One-on-One AI Immigration Case Call — Service Design

**Version:** 1.0  
**Date:** 2025  
**Status:** Design-Ready Implementation Plan  
**Author:** Lead Principal Engineer

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Core Design Principles](#3-core-design-principles)
4. [Data Models](#4-data-models)
5. [Service Layer Design](#5-service-layer-design)
6. [API Specification](#6-api-specification)
7. [Integration Points](#7-integration-points)
8. [Security & Compliance](#8-security--compliance)
9. [Implementation Plan](#9-implementation-plan)
10. [Directory Structure](#10-directory-structure)

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
| External meeting tool | Native, controlled environment |
| Broad questioning | Strictly scoped to immigration case |
| No persistent context | Case timeline integration |
| Hard to audit | Fully logged & reviewable |

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

---

## 4. Data Models

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
    
    ai_prompt_used = models.TextField(
        null=True,
        blank=True,
        help_text="Full prompt sent to AI (for audit)"
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

## 5. Service Layer Design

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
        1. Build case context (CaseContextBuilder)
        2. Seal context bundle
        3. Update status to 'ready'
        
        Returns:
        - CallSession in 'ready' status
        """
    
    @staticmethod
    def start_call(session_id: str) -> Optional[CallSession]:
        """
        Start the call.
        
        Steps:
        1. Validate session is 'ready'
        2. Initialize WebRTC session
        3. Start timebox timer
        4. Update status to 'in_progress'
        5. Record started_at timestamp
        
        Returns:
        - CallSession in 'in_progress' status
        """
    
    @staticmethod
    def end_call(session_id: str, reason: str = 'completed') -> Optional[CallSession]:
        """
        End the call normally.
        
        Steps:
        1. Validate session is 'in_progress'
        2. Stop timebox timer
        3. Generate post-call summary
        4. Attach summary to case timeline
        5. Update status to 'completed'
        6. Record ended_at and duration_seconds
        
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
    def build_context_bundle(case_id: str) -> Dict[str, Any]:
        """
        Build comprehensive case context bundle.
        
        Includes:
        - Case metadata (type, status, jurisdiction)
        - Case facts (all facts from CaseFact model)
        - Documents summary (uploaded documents, status)
        - Human review notes (if any)
        - AI decisions (eligibility results, confidence scores)
        - Applicable rules (visa requirements, document requirements)
        - Outstanding issues/flags
        
        Returns:
        - Sealed context bundle (dict)
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
    def generate_ai_response(user_text: str, session_id: str) -> Dict[str, Any]:
        """
        Generate AI response to user input.
        
        Steps:
        1. Validate user input against guardrails
        2. Build AI prompt with context bundle
        3. Call LLM API
        4. Validate AI response against guardrails
        5. Create CallTranscript entry (AI turn)
        6. Convert text to speech
        7. Return audio + text
        
        Returns:
        - Dict with 'text', 'audio', 'turn_id', 'guardrails_triggered'
        """
    
    @staticmethod
    def handle_interruption(session_id: str):
        """Handle user interruption during AI response."""
```

### 5.4 TimeboxService

**Responsibilities**:
- Enforce 30-minute limit
- Provide warnings
- Auto-terminate at limit

**Key Methods**:

```python
class TimeboxService:
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
    def auto_terminate_if_needed(session_id: str) -> Optional[CallSession]:
        """
        Auto-terminate call if 30 minutes reached.
        
        Called by background task or on each turn.
        """
```

### 5.5 GuardrailsService

**Responsibilities**:
- Validate user questions against case scope
- Validate AI responses for compliance
- Trigger refusals/warnings/escalations

**Key Methods**:

```python
class GuardrailsService:
    @staticmethod
    def validate_user_input(user_text: str, context_bundle: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate user input against case scope.
        
        Returns:
        - Tuple of (is_valid, error_message, action)
        - Actions: 'allow', 'refuse', 'warn', 'escalate'
        """
    
    @staticmethod
    def validate_ai_response(ai_text: str, context_bundle: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate AI response for compliance.
        
        Checks:
        - No legal advice language
        - Stays within case scope
        - Uses safety language
        - No guarantees or promises
        
        Returns:
        - Tuple of (is_valid, error_message, action)
        """
    
    @staticmethod
    def generate_refusal_message(off_scope_topic: str) -> str:
        """Generate polite refusal message for off-scope questions."""
    
    @staticmethod
    def generate_safety_language() -> str:
        """Generate safety language prefix for AI responses."""
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

---

## 6. API Specification

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

## 7. Integration Points

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

## 8. Security & Compliance

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

## 9. Implementation Plan

### 9.1 Phase 1: Core Infrastructure (Week 1-2)

**Week 1**:
1. Create models (CallSession, CallTranscript, CallAuditLog, CallSummary)
2. Create migrations
3. Create repositories and selectors
4. Create serializers
5. Write unit tests for models

**Week 2**:
1. Implement CallSessionService (create, prepare, start, end, terminate)
2. Implement CaseContextBuilder
3. Implement basic guardrails validation
4. Write unit tests for services

### 9.2 Phase 2: Voice Integration (Week 3-4)

**Week 3**:
1. Integrate speech-to-text service (Google Speech-to-Text or AWS Transcribe)
2. Integrate text-to-speech service (Google TTS or AWS Polly)
3. Implement VoiceOrchestrator
4. Write integration tests

**Week 4**:
1. Implement WebRTC or managed voice provider integration
2. Implement turn-taking logic
3. Implement interruption handling
4. Write end-to-end tests

### 9.3 Phase 3: Timebox & Guardrails (Week 5)

**Week 5**:
1. Implement TimeboxService (30-minute enforcement)
2. Implement GuardrailsService (scope validation, compliance checks)
3. Implement warning system (5 min, 1 min)
4. Implement auto-termination
5. Write tests

### 9.4 Phase 4: Post-Call & Admin (Week 6)

**Week 6**:
1. Implement PostCallSummaryService
2. Implement summary attachment to case timeline
3. Create admin views (list, detail, analytics)
4. Create admin serializers
5. Write tests

### 9.5 Phase 5: Polish & Production (Week 7-8)

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

## 10. Directory Structure

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
│   └── voice_utils.py
├── signals/
│   ├── __init__.py
│   └── call_session_signals.py
├── tasks/
│   ├── __init__.py
│   └── timebox_tasks.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

---

## 11. Key Implementation Details

### 11.1 Context Bundle Structure

```python
{
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

### 11.2 Guardrails Validation Examples

**Off-Scope Question**:
- User: "Can I switch to a work visa?"
- Guardrails: Refuse (off-scope)
- AI Response: "I can only discuss information related to your current Student Visa case. For questions about other visa types, please consult a qualified immigration adviser."

**Legal Advice Attempt**:
- User: "Will my application be approved?"
- Guardrails: Refuse (no guarantees)
- AI Response: "I cannot provide guarantees about application outcomes. Based on your case information, you appear to meet the requirements, but final decisions are made by immigration authorities."

**Safe Question**:
- User: "What documents do I need?"
- Guardrails: Allow
- AI Response: "Based on your case information, you need: [list from context bundle]..."

### 11.3 Timebox Warnings

**5 Minutes Remaining**:
- System message: "You have 5 minutes remaining in this call."
- Visual indicator: Yellow warning badge

**1 Minute Remaining**:
- System message: "You have 1 minute remaining. The call will end automatically."
- Visual indicator: Red warning badge

**Auto-Termination**:
- System message: "Your 30-minute call has ended. A summary will be available shortly."
- Call status: 'completed'
- Summary generation triggered

### 11.4 Post-Call Summary Example

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

---

## 12. Testing Strategy

### 12.1 Unit Tests

- Model validation tests
- Service method tests
- Guardrails validation tests
- Context builder tests
- Timebox service tests

### 12.2 Integration Tests

- End-to-end call flow (create → prepare → start → end)
- Voice processing integration
- Case context building integration
- Post-call summary generation

### 12.3 Compliance Tests

- Guardrails enforcement
- Refusal message generation
- Safety language enforcement
- Audit log completeness

---

## 13. Monitoring & Observability

### 13.1 Metrics

- Call creation rate
- Call completion rate
- Average call duration
- Guardrails trigger rate
- Auto-termination rate
- Voice processing latency

### 13.2 Alerts

- High guardrails trigger rate (>20%)
- Voice processing failures
- Timebox enforcement failures
- Context building failures

### 13.3 Logging

- All call events logged to `CallAuditLog`
- Integration with `AuditLogService` for system-wide audit
- Error logging with full context

---

## 14. Future Enhancements

### 14.1 Phase 2 Features

- Multi-language support
- Call recording (with user consent)
- Call replay functionality
- Advanced analytics dashboard

### 14.2 Phase 3 Features

- Proactive AI suggestions during call
- Real-time document validation during call
- Integration with payment system for premium calls
- Mobile app support

---

## 15. Compliance Notes

### 15.1 OISC Boundaries

- Clear "Not Legal Advice" disclaimers
- Informational guidance only
- Escalation to human reviewers for complex cases
- Full audit trail for compliance review

### 15.2 GDPR Compliance

- Right to erasure for call data
- Data minimization (only store necessary data)
- Encryption at rest
- User consent for call recording (if implemented)

### 15.3 Accessibility

- Support for users with hearing impairments (transcript display)
- Support for users with speech impairments (text input option)
- WCAG 2.1 AA compliance

---

**Status**: Ready for Implementation  
**Next Steps**: 
1. Review and approve design
2. Create implementation tickets
3. Begin Phase 1 implementation
4. Set up voice infrastructure (WebRTC or managed provider)
