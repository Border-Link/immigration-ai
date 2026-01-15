"""
Prometheus Metrics for Rules Knowledge Module

Custom metrics for monitoring rules_knowledge operations.
Uses django_prometheus for metric collection.
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


# Rule Engine Metrics
if Counter and Histogram:
    rule_engine_evaluations_total = _safe_create_metric(
        Counter,
        'rules_knowledge_rule_engine_evaluations_total',
        'Total number of rule engine evaluations',
        ['visa_type', 'outcome']
    
    )

    
    rule_engine_evaluation_duration_seconds = _safe_create_metric(
        Histogram,
        'rules_knowledge_rule_engine_evaluation_duration_seconds',
        'Duration of rule engine evaluations in seconds',
        ['visa_type'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)  # Buckets for latency distribution
    )
    
    rule_engine_requirements_evaluated = _safe_create_metric(
        Histogram,
        'rules_knowledge_rule_engine_requirements_evaluated',
        'Number of requirements evaluated per rule engine call',
        ['visa_type'],
        buckets=(1, 5, 10, 20, 50, 100, 200)
    )
    
    # Rule Publishing Metrics
    rule_publishing_operations_total = _safe_create_metric(
        Counter,
        'rules_knowledge_rule_publishing_operations_total',
        'Total number of rule publishing operations',
        ['operation', 'status']
    
    )

    
    rule_publishing_duration_seconds = _safe_create_metric(
        Histogram,
        'rules_knowledge_rule_publishing_duration_seconds',
        'Duration of rule publishing operations in seconds',
        ['operation'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
    )
    
    # Cache Metrics
    cache_operations_total = _safe_create_metric(
        Counter,
        'rules_knowledge_cache_operations_total',
        'Total number of cache operations',
        ['operation', 'result']  # operation: get, set, delete; result: hit, miss, error
    )
    
    # API Endpoint Metrics (will be tracked via middleware or decorator)
    api_requests_total = _safe_create_metric(
        Counter,
        'rules_knowledge_api_requests_total',
        'Total number of API requests',
        ['endpoint', 'method', 'status_code']
    )

    api_request_duration_seconds = _safe_create_metric(
        Histogram,
        'rules_knowledge_api_request_duration_seconds',
        'Duration of API requests in seconds',
        ['endpoint', 'method'],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # Version Conflict Metrics
    version_conflicts_total = _safe_create_metric(
        Counter,
        'rules_knowledge_version_conflicts_total',
        'Total number of version conflicts detected (optimistic locking)',
        ['operation']  # operation: update, publish
    )
    
else:
    # Dummy metrics if prometheus_client not available
    rule_engine_evaluations_total = None
    rule_engine_evaluation_duration_seconds = None
    rule_engine_requirements_evaluated = None
    rule_publishing_operations_total = None
    rule_publishing_duration_seconds = None
    cache_operations_total = None
    api_requests_total = None
    api_request_duration_seconds = None
    version_conflicts_total = None


def track_rule_engine_evaluation(visa_type: str = 'unknown'):
    """
    Decorator to track rule engine evaluation metrics.
    
    Usage:
        @track_rule_engine_evaluation(visa_type='skilled_worker')
        def evaluate_all_requirements(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rule_engine_evaluation_duration_seconds:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Track success
                duration = time.time() - start_time
                rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type).observe(duration)
                
                # Track outcome if result has outcome attribute
                if hasattr(result, 'outcome'):
                    outcome = result.outcome
                    rule_engine_evaluations_total.labels(visa_type=visa_type, outcome=outcome).inc()
                    
                    # Track requirements evaluated
                    if hasattr(result, 'requirements_total'):
                        rule_engine_requirements_evaluated.labels(visa_type=visa_type).observe(
                            result.requirements_total
                        )
                else:
                    rule_engine_evaluations_total.labels(visa_type=visa_type, outcome='unknown').inc()
                
                return result
            except Exception as e:
                # Track failure
                duration = time.time() - start_time
                rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type).observe(duration)
                rule_engine_evaluations_total.labels(visa_type=visa_type, outcome='error').inc()
                raise
        
        return wrapper
    return decorator


def track_rule_publishing(operation: str = 'publish'):
    """
    Decorator to track rule publishing metrics.
    
    Usage:
        @track_rule_publishing(operation='publish')
        def publish_rule_version(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rule_publishing_duration_seconds:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Track success
                duration = time.time() - start_time
                rule_publishing_duration_seconds.labels(operation=operation).observe(duration)
                rule_publishing_operations_total.labels(operation=operation, status='success').inc()
                
                return result
            except Exception as e:
                # Track failure
                duration = time.time() - start_time
                rule_publishing_duration_seconds.labels(operation=operation).observe(duration)
                rule_publishing_operations_total.labels(operation=operation, status='failure').inc()
                raise
        
        return wrapper
    return decorator


def track_cache_operation(operation: str, result: str):
    """
    Track cache operations (hit/miss).
    
    Args:
        operation: 'get', 'set', 'delete'
        result: 'hit', 'miss', 'error', 'success'
    """
    if cache_operations_total:
        cache_operations_total.labels(operation=operation, result=result).inc()


def track_version_conflict(operation: str):
    """
    Track version conflicts (optimistic locking).
    
    Args:
        operation: 'update', 'publish'
    """
    if version_conflicts_total:
        version_conflicts_total.labels(operation=operation).inc()


def track_api_request(endpoint: str, method: str, status_code: int, duration: float):
    """
    Track API request metrics.
    
    Args:
        endpoint: API endpoint name (e.g., 'visa-type-list')
        method: HTTP method (e.g., 'GET', 'POST')
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    if api_requests_total and api_request_duration_seconds:
        api_requests_total.labels(endpoint=endpoint, method=method, status_code=str(status_code)).inc()
        api_request_duration_seconds.labels(endpoint=endpoint, method=method).observe(duration)
