"""
Prometheus Metrics for Compliance Module

Custom metrics for monitoring compliance operations including:
- Audit log operations
- Compliance checks
- Data retention operations
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


def _safe_create_metric(metric_class, name, *args, **kwargs):
    """
    Safely create a metric, returning None if it already exists.
    This prevents duplicate registration errors during module reloads.
    """
    if not metric_class:
        return None
    
    try:
        return metric_class(name, *args, **kwargs)
    except ValueError:
        # Metric already exists in registry, return None to use dummy
        # The existing metric will still work for tracking
        return None


# Audit Log Metrics
if Counter and Histogram:
    audit_log_entries_created_total = _safe_create_metric(
        Counter,
        'compliance_audit_log_entries_created_total',
        'Total number of audit log entries created',
        ['level', 'logger_name']  # level: INFO, WARNING, ERROR; logger_name: module name
    )
    
    audit_log_creation_duration_seconds = _safe_create_metric(
        Histogram,
        'compliance_audit_log_creation_duration_seconds',
        'Duration of audit log entry creation in seconds',
        [],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5)
    )
    
    audit_log_queries_total = _safe_create_metric(
        Counter,
        'compliance_audit_log_queries_total',
        'Total number of audit log queries',
        ['query_type']  # query_type: by_user, by_module, by_date_range, etc.
    )
    
    audit_log_query_duration_seconds = _safe_create_metric(
        Histogram,
        'compliance_audit_log_query_duration_seconds',
        'Duration of audit log queries in seconds',
        ['query_type'],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # Audit Log Storage Metrics
    audit_log_entries_by_level = _safe_create_metric(
        Gauge,
        'compliance_audit_log_entries_by_level',
        'Current number of audit log entries by level',
        ['level']
    )
    
    audit_log_entries_by_module = _safe_create_metric(
        Gauge,
        'compliance_audit_log_entries_by_module',
        'Current number of audit log entries by module',
        ['logger_name']
    )
    
    # Data Retention Metrics
    audit_log_retention_operations_total = _safe_create_metric(
        Counter,
        'compliance_audit_log_retention_operations_total',
        'Total number of audit log retention operations',
        ['operation', 'status']  # operation: archive, delete; status: success, failure
    )
    
    audit_log_retention_duration_seconds = _safe_create_metric(
        Histogram,
        'compliance_audit_log_retention_duration_seconds',
        'Duration of audit log retention operations in seconds',
        ['operation'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
    )
    
    audit_log_entries_archived_total = _safe_create_metric(
        Counter,
        'compliance_audit_log_entries_archived_total',
        'Total number of audit log entries archived',
        []
    )
    
    audit_log_entries_deleted_total = _safe_create_metric(
        Counter,
        'compliance_audit_log_entries_deleted_total',
        'Total number of audit log entries deleted',
        []
    )
    
else:
    # Dummy metrics
    audit_log_entries_created_total = None
    audit_log_creation_duration_seconds = None
    audit_log_queries_total = None
    audit_log_query_duration_seconds = None
    audit_log_entries_by_level = None
    audit_log_entries_by_module = None
    audit_log_retention_operations_total = None
    audit_log_retention_duration_seconds = None
    audit_log_entries_archived_total = None
    audit_log_entries_deleted_total = None


def track_audit_log_creation(level: str, logger_name: str, duration: float):
    """Track audit log entry creation."""
    if audit_log_entries_created_total:
        audit_log_entries_created_total.labels(level=level, logger_name=logger_name).inc()
    if audit_log_creation_duration_seconds:
        audit_log_creation_duration_seconds.observe(duration)


def track_audit_log_query(query_type: str, duration: float):
    """Track audit log query."""
    if audit_log_queries_total:
        audit_log_queries_total.labels(query_type=query_type).inc()
    if audit_log_query_duration_seconds:
        audit_log_query_duration_seconds.labels(query_type=query_type).observe(duration)


def update_audit_log_entries_by_level(level: str, count: int):
    """Update audit log entries by level gauge."""
    if audit_log_entries_by_level:
        audit_log_entries_by_level.labels(level=level).set(count)


def update_audit_log_entries_by_module(logger_name: str, count: int):
    """Update audit log entries by module gauge."""
    if audit_log_entries_by_module:
        audit_log_entries_by_module.labels(logger_name=logger_name).set(count)


def track_audit_log_retention(operation: str, status: str, duration: float, entries_count: int = None):
    """Track audit log retention operation."""
    if audit_log_retention_operations_total:
        audit_log_retention_operations_total.labels(operation=operation, status=status).inc()
    if audit_log_retention_duration_seconds:
        audit_log_retention_duration_seconds.labels(operation=operation).observe(duration)
    if operation == 'archive' and audit_log_entries_archived_total and entries_count:
        audit_log_entries_archived_total.inc(entries_count)
    if operation == 'delete' and audit_log_entries_deleted_total and entries_count:
        audit_log_entries_deleted_total.inc(entries_count)
