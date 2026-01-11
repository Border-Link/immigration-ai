"""
Prometheus Metrics for Immigration Cases Module

Custom metrics for monitoring immigration cases operations including:
- Case creation and updates
- Status transitions
- Case facts management
- Status history tracking
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


# Case Management Metrics
if Counter and Histogram:
    case_creations_total = Counter(
        'immigration_cases_case_creations_total',
        'Total number of case creations',
        ['jurisdiction', 'status']  # status: draft, etc.
    )
    
    case_updates_total = Counter(
        'immigration_cases_case_updates_total',
        'Total number of case updates',
        ['operation']  # operation: status_change, fact_update, general_update
    )
    
    case_status_transitions_total = Counter(
        'immigration_cases_case_status_transitions_total',
        'Total number of case status transitions',
        ['from_status', 'to_status']  # e.g., draft -> evaluated
    )
    
    case_status_transition_duration_seconds = Histogram(
        'immigration_cases_case_status_transition_duration_seconds',
        'Duration of case status transitions in seconds',
        ['to_status'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # Case Facts Metrics
    case_facts_added_total = Counter(
        'immigration_cases_case_facts_added_total',
        'Total number of case facts added',
        ['fact_type']  # fact_type: age, salary, nationality, etc.
    )
    
    case_facts_updated_total = Counter(
        'immigration_cases_case_facts_updated_total',
        'Total number of case facts updated',
        ['fact_type']
    )
    
    case_facts_per_case = Histogram(
        'immigration_cases_case_facts_per_case',
        'Number of facts per case',
        [],
        buckets=(1, 5, 10, 20, 50, 100)
    )
    
    # Version Conflict Metrics
    case_version_conflicts_total = Counter(
        'immigration_cases_case_version_conflicts_total',
        'Total number of version conflicts (optimistic locking)',
        ['operation']  # operation: update, status_change
    )
    
    # Status History Metrics
    case_status_history_entries_total = Counter(
        'immigration_cases_case_status_history_entries_total',
        'Total number of status history entries created',
        ['to_status']
    )
    
    # Case Lifecycle Metrics
    case_lifecycle_duration_days = Histogram(
        'immigration_cases_case_lifecycle_duration_days',
        'Duration of case lifecycle in days',
        ['final_status'],  # final_status: closed, abandoned, etc.
        buckets=(1, 7, 30, 90, 180, 365, 730)
    )
    
    cases_by_status = Gauge(
        'immigration_cases_cases_by_status',
        'Current number of cases by status',
        ['status', 'jurisdiction']
    )
    
else:
    # Dummy metrics
    case_creations_total = None
    case_updates_total = None
    case_status_transitions_total = None
    case_status_transition_duration_seconds = None
    case_facts_added_total = None
    case_facts_updated_total = None
    case_facts_per_case = None
    case_version_conflicts_total = None
    case_status_history_entries_total = None
    case_lifecycle_duration_days = None
    cases_by_status = None


def track_case_creation(jurisdiction: str, status: str):
    """Track case creation."""
    if case_creations_total:
        case_creations_total.labels(jurisdiction=jurisdiction, status=status).inc()


def track_case_update(operation: str):
    """Track case update."""
    if case_updates_total:
        case_updates_total.labels(operation=operation).inc()


def track_case_status_transition(from_status: str, to_status: str, duration: float):
    """Track case status transition."""
    if case_status_transitions_total:
        case_status_transitions_total.labels(from_status=from_status, to_status=to_status).inc()
    
    if case_status_transition_duration_seconds:
        case_status_transition_duration_seconds.labels(to_status=to_status).observe(duration)


def track_case_fact_added(fact_type: str):
    """Track case fact addition."""
    if case_facts_added_total:
        case_facts_added_total.labels(fact_type=fact_type).inc()


def track_case_fact_updated(fact_type: str):
    """Track case fact update."""
    if case_facts_updated_total:
        case_facts_updated_total.labels(fact_type=fact_type).inc()


def track_case_facts_count(count: int):
    """Track number of facts per case."""
    if case_facts_per_case:
        case_facts_per_case.observe(count)


def track_case_version_conflict(operation: str):
    """Track version conflict."""
    if case_version_conflicts_total:
        case_version_conflicts_total.labels(operation=operation).inc()


def track_case_status_history(to_status: str):
    """Track status history entry creation."""
    if case_status_history_entries_total:
        case_status_history_entries_total.labels(to_status=to_status).inc()


def update_cases_by_status(status: str, jurisdiction: str, count: int):
    """Update gauge for cases by status."""
    if cases_by_status:
        cases_by_status.labels(status=status, jurisdiction=jurisdiction).set(count)
