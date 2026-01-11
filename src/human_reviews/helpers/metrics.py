"""
Prometheus Metrics for Human Reviews Module

Custom metrics for monitoring human review operations including:
- Review creation and assignment
- Review status transitions
- Decision overrides
- Review notes
- Reviewer workload
"""
import time
from functools import wraps

# Import prometheus_client for custom metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    Counter = None
    Histogram = None
    Gauge = None


# Review Management Metrics
if Counter and Histogram:
    review_creations_total = Counter(
        'human_reviews_review_creations_total',
        'Total number of review creations',
        ['assignment_type']  # assignment_type: manual, auto, round_robin, workload
    )
    
    review_assignments_total = Counter(
        'human_reviews_review_assignments_total',
        'Total number of review assignments',
        ['assignment_strategy']  # assignment_strategy: round_robin, workload, manual
    )
    
    review_status_transitions_total = Counter(
        'human_reviews_review_status_transitions_total',
        'Total number of review status transitions',
        ['from_status', 'to_status']  # e.g., pending -> in_progress -> completed
    )
    
    review_completion_duration_seconds = Histogram(
        'human_reviews_review_completion_duration_seconds',
        'Duration from review creation to completion in seconds',
        ['final_status'],  # final_status: approved, rejected, etc.
        buckets=(60, 300, 600, 1800, 3600, 7200, 86400)  # 1 min to 1 day
    )
    
    review_processing_duration_seconds = Histogram(
        'human_reviews_review_processing_duration_seconds',
        'Duration of active review processing in seconds',
        [],
        buckets=(60, 300, 600, 1800, 3600, 7200)
    )
    
    # Decision Override Metrics
    decision_overrides_total = Counter(
        'human_reviews_decision_overrides_total',
        'Total number of decision overrides',
        ['override_type', 'original_outcome', 'new_outcome']  # override_type: ai_override, rule_override
    )
    
    decision_override_duration_seconds = Histogram(
        'human_reviews_decision_override_duration_seconds',
        'Duration of decision override operations in seconds',
        ['override_type'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # Review Note Metrics
    review_notes_created_total = Counter(
        'human_reviews_review_notes_created_total',
        'Total number of review notes created',
        ['note_type']  # note_type: general, issue, clarification
    )
    
    review_notes_per_review = Histogram(
        'human_reviews_review_notes_per_review',
        'Number of notes per review',
        [],
        buckets=(0, 1, 2, 5, 10, 20)
    )
    
    # Reviewer Workload Metrics
    reviewer_workload = Gauge(
        'human_reviews_reviewer_workload',
        'Current workload (number of assigned reviews) per reviewer',
        ['reviewer_id', 'status']  # status: pending, in_progress
    )
    
    reviews_by_status = Gauge(
        'human_reviews_reviews_by_status',
        'Current number of reviews by status',
        ['status']
    )
    
    # Review Escalation Metrics
    review_escalations_total = Counter(
        'human_reviews_review_escalations_total',
        'Total number of review escalations',
        ['reason']  # reason: complexity, conflict, timeout
    )
    
    # Review Reassignment Metrics
    review_reassignments_total = Counter(
        'human_reviews_review_reassignments_total',
        'Total number of review reassignments',
        ['reason']  # reason: workload, expertise, availability
    )
    
    # Version Conflict Metrics
    review_version_conflicts_total = Counter(
        'human_reviews_review_version_conflicts_total',
        'Total number of version conflicts (optimistic locking)',
        ['operation']  # operation: update, status_change
    )
    
else:
    # Dummy metrics
    review_creations_total = None
    review_assignments_total = None
    review_status_transitions_total = None
    review_completion_duration_seconds = None
    review_processing_duration_seconds = None
    decision_overrides_total = None
    decision_override_duration_seconds = None
    review_notes_created_total = None
    review_notes_per_review = None
    reviewer_workload = None
    reviews_by_status = None
    review_escalations_total = None
    review_reassignments_total = None
    review_version_conflicts_total = None


def track_review_creation(assignment_type: str):
    """Track review creation."""
    if review_creations_total:
        review_creations_total.labels(assignment_type=assignment_type).inc()


def track_review_assignment(assignment_strategy: str):
    """Track review assignment."""
    if review_assignments_total:
        review_assignments_total.labels(assignment_strategy=assignment_strategy).inc()


def track_review_status_transition(from_status: str, to_status: str):
    """Track review status transition."""
    if review_status_transitions_total:
        review_status_transitions_total.labels(from_status=from_status, to_status=to_status).inc()


def track_review_completion(final_status: str, duration: float):
    """Track review completion."""
    if review_completion_duration_seconds:
        review_completion_duration_seconds.labels(final_status=final_status).observe(duration)


def track_review_processing(duration: float):
    """Track review processing duration."""
    if review_processing_duration_seconds:
        review_processing_duration_seconds.observe(duration)


def track_decision_override(override_type: str, original_outcome: str, new_outcome: str, duration: float):
    """Track decision override."""
    if decision_overrides_total:
        decision_overrides_total.labels(
            override_type=override_type,
            original_outcome=original_outcome,
            new_outcome=new_outcome
        ).inc()
    if decision_override_duration_seconds:
        decision_override_duration_seconds.labels(override_type=override_type).observe(duration)


def track_review_note_created(note_type: str):
    """Track review note creation."""
    if review_notes_created_total:
        review_notes_created_total.labels(note_type=note_type).inc()


def track_review_notes_count(count: int):
    """Track number of notes per review."""
    if review_notes_per_review:
        review_notes_per_review.observe(count)


def update_reviewer_workload(reviewer_id: str, status: str, count: int):
    """Update reviewer workload gauge."""
    if reviewer_workload:
        reviewer_workload.labels(reviewer_id=reviewer_id, status=status).set(count)


def update_reviews_by_status(status: str, count: int):
    """Update reviews by status gauge."""
    if reviews_by_status:
        reviews_by_status.labels(status=status).set(count)


def track_review_escalation(reason: str):
    """Track review escalation."""
    if review_escalations_total:
        review_escalations_total.labels(reason=reason).inc()


def track_review_reassignment(reason: str):
    """Track review reassignment."""
    if review_reassignments_total:
        review_reassignments_total.labels(reason=reason).inc()


def track_review_version_conflict(operation: str):
    """Track review version conflict."""
    if review_version_conflicts_total:
        review_version_conflicts_total.labels(operation=operation).inc()
