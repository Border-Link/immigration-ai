"""
Prometheus Metrics for Document Processing Module

Custom metrics for monitoring document processing operations including:
- Processing job creation and execution
- Processing job retries
- Processing job timeouts
- Processing history tracking
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


# Processing Job Metrics
if Counter and Histogram:
    processing_jobs_created_total = Counter(
        'document_processing_processing_jobs_created_total',
        'Total number of processing jobs created',
        ['processing_type', 'priority']  # processing_type: ocr, validation, etc.; priority: 1-10
    )
    
    processing_jobs_completed_total = Counter(
        'document_processing_processing_jobs_completed_total',
        'Total number of processing jobs completed',
        ['processing_type', 'status']  # status: success, failure
    )
    
    processing_job_duration_seconds = Histogram(
        'document_processing_processing_job_duration_seconds',
        'Duration of processing job execution in seconds',
        ['processing_type', 'status'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0)
    )
    
    # Processing Job Retry Metrics
    processing_job_retries_total = Counter(
        'document_processing_processing_job_retries_total',
        'Total number of processing job retries',
        ['processing_type', 'retry_reason']  # retry_reason: failure, timeout, error
    )
    
    processing_job_retry_duration_seconds = Histogram(
        'document_processing_processing_job_retry_duration_seconds',
        'Duration of processing job retry operations in seconds',
        [],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # Processing Job Timeout Metrics
    processing_job_timeouts_total = Counter(
        'document_processing_processing_job_timeouts_total',
        'Total number of processing job timeouts',
        ['processing_type']
    )
    
    # Processing Job Queue Metrics
    processing_jobs_by_status = Gauge(
        'document_processing_processing_jobs_by_status',
        'Current number of processing jobs by status',
        ['status', 'processing_type']  # status: pending, processing, completed, failed
    )
    
    processing_jobs_by_priority = Gauge(
        'document_processing_processing_jobs_by_priority',
        'Current number of processing jobs by priority',
        ['priority']
    )
    
    # Processing History Metrics
    processing_history_entries_total = Counter(
        'document_processing_processing_history_entries_total',
        'Total number of processing history entries created',
        ['status']  # status: success, failure
    )
    
else:
    # Dummy metrics
    processing_jobs_created_total = None
    processing_jobs_completed_total = None
    processing_job_duration_seconds = None
    processing_job_retries_total = None
    processing_job_retry_duration_seconds = None
    processing_job_timeouts_total = None
    processing_jobs_by_status = None
    processing_jobs_by_priority = None
    processing_history_entries_total = None


def track_processing_job_created(processing_type: str, priority: int):
    """Track processing job creation."""
    if processing_jobs_created_total:
        processing_jobs_created_total.labels(processing_type=processing_type, priority=str(priority)).inc()


def track_processing_job_completed(processing_type: str, status: str, duration: float):
    """Track processing job completion."""
    if processing_jobs_completed_total:
        processing_jobs_completed_total.labels(processing_type=processing_type, status=status).inc()
    if processing_job_duration_seconds:
        processing_job_duration_seconds.labels(processing_type=processing_type, status=status).observe(duration)


def track_processing_job_retry(processing_type: str, retry_reason: str, duration: float):
    """Track processing job retry."""
    if processing_job_retries_total:
        processing_job_retries_total.labels(processing_type=processing_type, retry_reason=retry_reason).inc()
    if processing_job_retry_duration_seconds:
        processing_job_retry_duration_seconds.observe(duration)


def track_processing_job_timeout(processing_type: str):
    """Track processing job timeout."""
    if processing_job_timeouts_total:
        processing_job_timeouts_total.labels(processing_type=processing_type).inc()


def update_processing_jobs_by_status(status: str, processing_type: str, count: int):
    """Update processing jobs by status gauge."""
    if processing_jobs_by_status:
        processing_jobs_by_status.labels(status=status, processing_type=processing_type).set(count)


def update_processing_jobs_by_priority(priority: int, count: int):
    """Update processing jobs by priority gauge."""
    if processing_jobs_by_priority:
        processing_jobs_by_priority.labels(priority=str(priority)).set(count)


def track_processing_history_entry(status: str):
    """Track processing history entry creation."""
    if processing_history_entries_total:
        processing_history_entries_total.labels(status=status).inc()
