"""
Prometheus Metrics for Data Ingestion Module

Custom metrics for monitoring data ingestion operations including:
- Document ingestion from sources
- Document parsing (AI-powered)
- Rule validation
- Document versioning and diff detection
- Data source management
"""
import time
from functools import wraps

# Import prometheus_client for custom metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    # Fallback if prometheus_client not available
    Counter = None
    Histogram = None
    Gauge = None


# Document Ingestion Metrics
if Counter and Histogram:
    document_ingestions_total = Counter(
        'data_ingestion_document_ingestions_total',
        'Total number of document ingestion operations',
        ['source_type', 'status']  # source_type: gov_uk, api, manual; status: success, failure
    )
    
    document_ingestion_duration_seconds = Histogram(
        'data_ingestion_document_ingestion_duration_seconds',
        'Duration of document ingestion operations in seconds',
        ['source_type'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
    )
    
    document_ingestion_size_bytes = Histogram(
        'data_ingestion_document_ingestion_size_bytes',
        'Size of ingested documents in bytes',
        ['source_type'],
        buckets=(1024, 10240, 102400, 1048576, 10485760, 104857600)  # 1KB to 100MB
    )
    
    # Document Parsing Metrics
    document_parsing_operations_total = Counter(
        'data_ingestion_document_parsing_operations_total',
        'Total number of document parsing operations',
        ['status', 'jurisdiction']  # status: success, failure, partial
    )
    
    document_parsing_duration_seconds = Histogram(
        'data_ingestion_document_parsing_duration_seconds',
        'Duration of document parsing operations in seconds',
        ['jurisdiction'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
    )
    
    document_parsing_rules_created = Histogram(
        'data_ingestion_document_parsing_rules_created',
        'Number of rules created per document parsing operation',
        ['jurisdiction'],
        buckets=(1, 5, 10, 20, 50, 100, 200)
    )
    
    document_parsing_tokens_used = Histogram(
        'data_ingestion_document_parsing_tokens_used',
        'Number of tokens used in document parsing',
        ['token_type'],  # token_type: prompt, completion, total
        buckets=(1000, 5000, 10000, 20000, 50000, 100000, 200000)
    )
    
    document_parsing_cost_usd = Histogram(
        'data_ingestion_document_parsing_cost_usd',
        'Cost of document parsing operations in USD',
        [],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # Rule Validation Metrics
    rule_validations_total = Counter(
        'data_ingestion_rule_validations_total',
        'Total number of rule validation operations',
        ['status', 'validation_type']  # status: approved, rejected, pending; validation_type: automated, manual
    )
    
    rule_validation_duration_seconds = Histogram(
        'data_ingestion_rule_validation_duration_seconds',
        'Duration of rule validation operations in seconds',
        ['validation_type'],
        buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0)
    )
    
    # Document Versioning Metrics
    document_versions_created_total = Counter(
        'data_ingestion_document_versions_created_total',
        'Total number of document versions created',
        ['source_type']
    )
    
    document_diff_detections_total = Counter(
        'data_ingestion_document_diff_detections_total',
        'Total number of document diff detections',
        ['has_changes']  # has_changes: true, false
    )
    
    document_diff_detection_duration_seconds = Histogram(
        'data_ingestion_document_diff_detection_duration_seconds',
        'Duration of document diff detection in seconds',
        [],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    document_diff_changes_detected = Histogram(
        'data_ingestion_document_diff_changes_detected',
        'Number of changes detected per document diff',
        [],
        buckets=(1, 5, 10, 20, 50, 100, 200)
    )
    
    # Document Chunking Metrics
    document_chunks_created_total = Counter(
        'data_ingestion_document_chunks_created_total',
        'Total number of document chunks created',
        ['chunking_strategy']  # chunking_strategy: fixed_size, semantic, etc.
    )
    
    document_chunking_duration_seconds = Histogram(
        'data_ingestion_document_chunking_duration_seconds',
        'Duration of document chunking operations in seconds',
        ['chunking_strategy'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    document_chunks_per_document = Histogram(
        'data_ingestion_document_chunks_per_document',
        'Number of chunks created per document',
        [],
        buckets=(1, 5, 10, 20, 50, 100, 200, 500)
    )
    
    # Data Source Metrics
    data_source_fetches_total = Counter(
        'data_ingestion_data_source_fetches_total',
        'Total number of data source fetch operations',
        ['source_type', 'status']  # status: success, failure, timeout
    )
    
    data_source_fetch_duration_seconds = Histogram(
        'data_ingestion_data_source_fetch_duration_seconds',
        'Duration of data source fetch operations in seconds',
        ['source_type'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
    )
    
    # Batch Processing Metrics
    batch_processing_operations_total = Counter(
        'data_ingestion_batch_processing_operations_total',
        'Total number of batch processing operations',
        ['status']  # status: success, failure, partial
    )
    
    batch_processing_duration_seconds = Histogram(
        'data_ingestion_batch_processing_duration_seconds',
        'Duration of batch processing operations in seconds',
        [],
        buckets=(10.0, 30.0, 60.0, 300.0, 600.0, 1800.0)
    )
    
    batch_processing_items_processed = Histogram(
        'data_ingestion_batch_processing_items_processed',
        'Number of items processed per batch operation',
        [],
        buckets=(1, 5, 10, 20, 50, 100, 200, 500)
    )
    
else:
    # Dummy metrics if prometheus_client not available
    document_ingestions_total = None
    document_ingestion_duration_seconds = None
    document_ingestion_size_bytes = None
    document_parsing_operations_total = None
    document_parsing_duration_seconds = None
    document_parsing_rules_created = None
    document_parsing_tokens_used = None
    document_parsing_cost_usd = None
    rule_validations_total = None
    rule_validation_duration_seconds = None
    document_versions_created_total = None
    document_diff_detections_total = None
    document_diff_detection_duration_seconds = None
    document_diff_changes_detected = None
    document_chunks_created_total = None
    document_chunking_duration_seconds = None
    document_chunks_per_document = None
    data_source_fetches_total = None
    data_source_fetch_duration_seconds = None
    batch_processing_operations_total = None
    batch_processing_duration_seconds = None
    batch_processing_items_processed = None


def track_document_ingestion(source_type: str, status: str, duration: float, size_bytes: int = None):
    """
    Track document ingestion metrics.
    
    Args:
        source_type: 'gov_uk', 'api', 'manual'
        status: 'success', 'failure'
        duration: Ingestion duration in seconds
        size_bytes: Document size in bytes
    """
    if document_ingestions_total:
        document_ingestions_total.labels(source_type=source_type, status=status).inc()
    
    if document_ingestion_duration_seconds:
        document_ingestion_duration_seconds.labels(source_type=source_type).observe(duration)
    
    if document_ingestion_size_bytes and size_bytes:
        document_ingestion_size_bytes.labels(source_type=source_type).observe(size_bytes)


def track_document_parsing(status: str, jurisdiction: str, duration: float, rules_created: int = None, tokens_prompt: int = None, tokens_completion: int = None, cost_usd: float = None):
    """
    Track document parsing metrics.
    
    Args:
        status: 'success', 'failure', 'partial'
        jurisdiction: Jurisdiction code (e.g., 'UK', 'US')
        duration: Parsing duration in seconds
        rules_created: Number of rules created
        tokens_prompt: Number of prompt tokens
        tokens_completion: Number of completion tokens
        cost_usd: Cost in USD
    """
    if document_parsing_operations_total:
        document_parsing_operations_total.labels(status=status, jurisdiction=jurisdiction).inc()
    
    if document_parsing_duration_seconds:
        document_parsing_duration_seconds.labels(jurisdiction=jurisdiction).observe(duration)
    
    if document_parsing_rules_created and rules_created:
        document_parsing_rules_created.labels(jurisdiction=jurisdiction).observe(rules_created)
    
    if document_parsing_tokens_used and tokens_prompt:
        document_parsing_tokens_used.labels(token_type='prompt').observe(tokens_prompt)
    if document_parsing_tokens_used and tokens_completion:
        document_parsing_tokens_used.labels(token_type='completion').observe(tokens_completion)
    if document_parsing_tokens_used and tokens_prompt and tokens_completion:
        document_parsing_tokens_used.labels(token_type='total').observe(tokens_prompt + tokens_completion)
    
    if document_parsing_cost_usd and cost_usd:
        document_parsing_cost_usd.observe(cost_usd)


def track_rule_validation(status: str, validation_type: str, duration: float):
    """
    Track rule validation metrics.
    
    Args:
        status: 'approved', 'rejected', 'pending'
        validation_type: 'automated', 'manual'
        duration: Validation duration in seconds
    """
    if rule_validations_total:
        rule_validations_total.labels(status=status, validation_type=validation_type).inc()
    
    if rule_validation_duration_seconds:
        rule_validation_duration_seconds.labels(validation_type=validation_type).observe(duration)


def track_document_version_creation(source_type: str):
    """
    Track document version creation.
    
    Args:
        source_type: Source type of the document
    """
    if document_versions_created_total:
        document_versions_created_total.labels(source_type=source_type).inc()


def track_document_diff(has_changes: bool, duration: float, changes_count: int = None):
    """
    Track document diff detection metrics.
    
    Args:
        has_changes: Whether changes were detected
        duration: Diff detection duration in seconds
        changes_count: Number of changes detected
    """
    if document_diff_detections_total:
        document_diff_detections_total.labels(has_changes=str(has_changes).lower()).inc()
    
    if document_diff_detection_duration_seconds:
        document_diff_detection_duration_seconds.observe(duration)
    
    if document_diff_changes_detected and changes_count:
        document_diff_changes_detected.observe(changes_count)


def track_document_chunking(chunking_strategy: str, duration: float, chunks_count: int):
    """
    Track document chunking metrics.
    
    Args:
        chunking_strategy: 'fixed_size', 'semantic', etc.
        duration: Chunking duration in seconds
        chunks_count: Number of chunks created
    """
    if document_chunks_created_total:
        document_chunks_created_total.labels(chunking_strategy=chunking_strategy).inc(chunks_count)
    
    if document_chunking_duration_seconds:
        document_chunking_duration_seconds.labels(chunking_strategy=chunking_strategy).observe(duration)
    
    if document_chunks_per_document:
        document_chunks_per_document.observe(chunks_count)


def track_data_source_fetch(source_type: str, status: str, duration: float):
    """
    Track data source fetch metrics.
    
    Args:
        source_type: Source type (e.g., 'gov_uk')
        status: 'success', 'failure', 'timeout'
        duration: Fetch duration in seconds
    """
    if data_source_fetches_total:
        data_source_fetches_total.labels(source_type=source_type, status=status).inc()
    
    if data_source_fetch_duration_seconds:
        data_source_fetch_duration_seconds.labels(source_type=source_type).observe(duration)


def track_batch_processing(status: str, duration: float, items_processed: int):
    """
    Track batch processing metrics.
    
    Args:
        status: 'success', 'failure', 'partial'
        duration: Processing duration in seconds
        items_processed: Number of items processed
    """
    if batch_processing_operations_total:
        batch_processing_operations_total.labels(status=status).inc()
    
    if batch_processing_duration_seconds:
        batch_processing_duration_seconds.observe(duration)
    
    if batch_processing_items_processed:
        batch_processing_items_processed.observe(items_processed)
