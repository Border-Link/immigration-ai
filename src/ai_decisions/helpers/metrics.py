"""
Prometheus Metrics for AI Decisions Module

Custom metrics for monitoring AI decisions operations including:
- Eligibility checks
- AI reasoning (RAG + LLM)
- Embedding generation
- Vector DB operations
- Citation tracking
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


# Eligibility Check Metrics
if Counter and Histogram:
    eligibility_checks_total = _safe_create_metric(
        Counter,
        'ai_decisions_eligibility_checks_total',
        'Total number of eligibility checks',
        ['outcome', 'requires_review', 'conflict_detected']  # outcome: likely, possible, unlikely; requires_review: true, false
    )
    
    eligibility_check_duration_seconds = _safe_create_metric(
        Histogram,
        'ai_decisions_eligibility_check_duration_seconds',
        'Duration of eligibility checks in seconds',
        ['outcome'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
    )
    
    eligibility_check_confidence = _safe_create_metric(
        Histogram,
        'ai_decisions_eligibility_check_confidence',
        'Confidence score distribution for eligibility checks',
        ['outcome'],
        buckets=(0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1.0)
    )
    
    # AI Reasoning Metrics
    ai_reasoning_calls_total = _safe_create_metric(
        Counter,
        'ai_decisions_ai_reasoning_calls_total',
        'Total number of AI reasoning calls',
        ['status', 'model']  # status: success, failure, timeout; model: gpt-4, claude, etc.
    )
    
    ai_reasoning_duration_seconds = _safe_create_metric(
        Histogram,
        'ai_decisions_ai_reasoning_duration_seconds',
        'Duration of AI reasoning calls in seconds',
        ['model', 'status'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
    )
    
    ai_reasoning_tokens_used = _safe_create_metric(
        Histogram,
        'ai_decisions_ai_reasoning_tokens_used',
        'Number of tokens used in AI reasoning calls',
        ['model', 'token_type'],  # token_type: prompt, completion, total
        buckets=(100, 500, 1000, 2000, 5000, 10000, 20000)
    )
    
    ai_reasoning_cost_usd = _safe_create_metric(
        Histogram,
        'ai_decisions_ai_reasoning_cost_usd',
        'Cost of AI reasoning calls in USD',
        ['model'],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # RAG/Vector DB Metrics
    vector_search_operations_total = _safe_create_metric(
        Counter,
        'ai_decisions_vector_search_operations_total',
        'Total number of vector similarity searches',
        ['status']  # status: success, failure
    )
    
    vector_search_duration_seconds = _safe_create_metric(
        Histogram,
        'ai_decisions_vector_search_duration_seconds',
        'Duration of vector similarity searches in seconds',
        ['status'],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0)
    )
    
    vector_search_results_count = _safe_create_metric(
        Histogram,
        'ai_decisions_vector_search_results_count',
        'Number of results returned from vector search',
        [],
        buckets=(1, 5, 10, 20, 50, 100)
    )
    
    vector_search_similarity_score = _safe_create_metric(
        Histogram,
        'ai_decisions_vector_search_similarity_score',
        'Similarity scores from vector search',
        [],
        buckets=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0)
    )
    
    # Embedding Metrics
    embedding_generations_total = _safe_create_metric(
        Counter,
        'ai_decisions_embedding_generations_total',
        'Total number of embedding generations',
        ['status', 'model']  # status: success, failure; model: text-embedding-ada-002, etc.
    )
    
    embedding_generation_duration_seconds = _safe_create_metric(
        Histogram,
        'ai_decisions_embedding_generation_duration_seconds',
        'Duration of embedding generation in seconds',
        ['model'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    embedding_dimensions = _safe_create_metric(
        Histogram,
        'ai_decisions_embedding_dimensions',
        'Dimensions of generated embeddings',
        ['model'],
        buckets=(128, 256, 512, 768, 1024, 1536, 2048)
    )
    
    # Citation Metrics
    citations_extracted_total = _safe_create_metric(
        Counter,
        'ai_decisions_citations_extracted_total',
        'Total number of citations extracted from AI responses',
        ['source_type']  # source_type: document, rule, policy
    )
    
    citations_per_reasoning = _safe_create_metric(
        Histogram,
        'ai_decisions_citations_per_reasoning',
        'Number of citations per AI reasoning call',
        [],
        buckets=(0, 1, 2, 5, 10, 20, 50)
    )
    
    # Conflict Detection Metrics
    eligibility_conflicts_total = _safe_create_metric(
        Counter,
        'ai_decisions_eligibility_conflicts_total',
        'Total number of conflicts between rule engine and AI reasoning',
        ['conflict_type']  # conflict_type: outcome_mismatch, confidence_gap, etc.
    )
    
    # Auto-escalation Metrics
    auto_escalations_total = _safe_create_metric(
        Counter,
        'ai_decisions_auto_escalations_total',
        'Total number of auto-escalations to human review',
        ['reason']  # reason: low_confidence, conflict, error
    )
    
else:
    # Dummy metrics if prometheus_client not available
    eligibility_checks_total = None
    eligibility_check_duration_seconds = None
    eligibility_check_confidence = None
    ai_reasoning_calls_total = None
    ai_reasoning_duration_seconds = None
    ai_reasoning_tokens_used = None
    ai_reasoning_cost_usd = None
    vector_search_operations_total = None
    vector_search_duration_seconds = None
    vector_search_results_count = None
    vector_search_similarity_score = None
    embedding_generations_total = None
    embedding_generation_duration_seconds = None
    embedding_dimensions = None
    citations_extracted_total = None
    citations_per_reasoning = None
    eligibility_conflicts_total = None
    auto_escalations_total = None


def track_eligibility_check(outcome: str, requires_review: bool, conflict_detected: bool, duration: float, confidence: float):
    """
    Track eligibility check metrics.
    
    Args:
        outcome: 'likely', 'possible', 'unlikely'
        requires_review: Whether human review is required
        conflict_detected: Whether conflict between rule engine and AI was detected
        duration: Check duration in seconds
        confidence: Confidence score (0.0 to 1.0)
    """
    if eligibility_checks_total:
        eligibility_checks_total.labels(
            outcome=outcome,
            requires_review=str(requires_review).lower(),
            conflict_detected=str(conflict_detected).lower()
        ).inc()
    
    if eligibility_check_duration_seconds:
        eligibility_check_duration_seconds.labels(outcome=outcome).observe(duration)
    
    if eligibility_check_confidence:
        eligibility_check_confidence.labels(outcome=outcome).observe(confidence)


def track_ai_reasoning(model: str, status: str, duration: float, tokens_prompt: int = None, tokens_completion: int = None, cost_usd: float = None):
    """
    Track AI reasoning call metrics.
    
    Args:
        model: Model name (e.g., 'gpt-4', 'claude-3')
        status: 'success', 'failure', 'timeout'
        duration: Call duration in seconds
        tokens_prompt: Number of prompt tokens
        tokens_completion: Number of completion tokens
        cost_usd: Cost in USD
    """
    if ai_reasoning_calls_total:
        ai_reasoning_calls_total.labels(status=status, model=model).inc()
    
    if ai_reasoning_duration_seconds:
        ai_reasoning_duration_seconds.labels(model=model, status=status).observe(duration)
    
    if ai_reasoning_tokens_used and tokens_prompt:
        ai_reasoning_tokens_used.labels(model=model, token_type='prompt').observe(tokens_prompt)
    if ai_reasoning_tokens_used and tokens_completion:
        ai_reasoning_tokens_used.labels(model=model, token_type='completion').observe(tokens_completion)
    if ai_reasoning_tokens_used and tokens_prompt and tokens_completion:
        ai_reasoning_tokens_used.labels(model=model, token_type='total').observe(tokens_prompt + tokens_completion)
    
    if ai_reasoning_cost_usd and cost_usd:
        ai_reasoning_cost_usd.labels(model=model).observe(cost_usd)


def track_vector_search(status: str, duration: float, results_count: int, similarity_scores: list = None):
    """
    Track vector search metrics.
    
    Args:
        status: 'success', 'failure'
        duration: Search duration in seconds
        results_count: Number of results returned
        similarity_scores: List of similarity scores
    """
    if vector_search_operations_total:
        vector_search_operations_total.labels(status=status).inc()
    
    if vector_search_duration_seconds:
        vector_search_duration_seconds.labels(status=status).observe(duration)
    
    if vector_search_results_count:
        vector_search_results_count.observe(results_count)
    
    if vector_search_similarity_score and similarity_scores:
        for score in similarity_scores:
            vector_search_similarity_score.observe(score)


def track_embedding_generation(model: str, status: str, duration: float, dimensions: int = None):
    """
    Track embedding generation metrics.
    
    Args:
        model: Model name (e.g., 'text-embedding-ada-002')
        status: 'success', 'failure'
        duration: Generation duration in seconds
        dimensions: Embedding dimensions
    """
    if embedding_generations_total:
        embedding_generations_total.labels(status=status, model=model).inc()
    
    if embedding_generation_duration_seconds:
        embedding_generation_duration_seconds.labels(model=model).observe(duration)
    
    if embedding_dimensions and dimensions:
        embedding_dimensions.labels(model=model).observe(dimensions)


def track_citations_extracted(source_type: str, count: int):
    """
    Track citation extraction metrics.
    
    Args:
        source_type: 'document', 'rule', 'policy'
        count: Number of citations extracted
    """
    if citations_extracted_total:
        citations_extracted_total.labels(source_type=source_type).inc(count)
    
    if citations_per_reasoning:
        citations_per_reasoning.observe(count)


def track_eligibility_conflict(conflict_type: str):
    """
    Track eligibility conflict detection.
    
    Args:
        conflict_type: 'outcome_mismatch', 'confidence_gap', etc.
    """
    if eligibility_conflicts_total:
        eligibility_conflicts_total.labels(conflict_type=conflict_type).inc()


def track_auto_escalation(reason: str):
    """
    Track auto-escalation to human review.
    
    Args:
        reason: 'low_confidence', 'conflict', 'error'
    """
    if auto_escalations_total:
        auto_escalations_total.labels(reason=reason).inc()
