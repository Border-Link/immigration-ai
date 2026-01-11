"""
Prometheus Metrics for Payments Module

Custom metrics for monitoring payment operations including:
- Payment creation
- Payment processing
- Payment status transitions
- Payment provider interactions
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


# Payment Management Metrics
if Counter and Histogram:
    payment_creations_total = Counter(
        'payments_payment_creations_total',
        'Total number of payment creations',
        ['currency', 'payment_provider']  # currency: GBP, USD, etc.; payment_provider: stripe, paypal, etc.
    )
    
    payment_amount_total = Histogram(
        'payments_payment_amount_total',
        'Payment amounts',
        ['currency'],
        buckets=(10, 30, 50, 100, 150, 300, 500, 1000)
    )
    
    payment_status_transitions_total = Counter(
        'payments_payment_status_transitions_total',
        'Total number of payment status transitions',
        ['from_status', 'to_status']  # e.g., pending -> processing -> completed
    )
    
    payment_processing_duration_seconds = Histogram(
        'payments_payment_processing_duration_seconds',
        'Duration of payment processing in seconds',
        ['payment_provider', 'final_status'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
    )
    
    # Payment Provider Metrics
    payment_provider_calls_total = Counter(
        'payments_payment_provider_calls_total',
        'Total number of payment provider API calls',
        ['provider', 'operation', 'status']  # operation: create, verify, refund; status: success, failure
    )
    
    payment_provider_call_duration_seconds = Histogram(
        'payments_payment_provider_call_duration_seconds',
        'Duration of payment provider API calls in seconds',
        ['provider', 'operation'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
    )
    
    # Payment Failure Metrics
    payment_failures_total = Counter(
        'payments_payment_failures_total',
        'Total number of payment failures',
        ['failure_reason', 'payment_provider']  # failure_reason: insufficient_funds, card_declined, etc.
    )
    
    # Payment Refund Metrics
    payment_refunds_total = Counter(
        'payments_payment_refunds_total',
        'Total number of payment refunds',
        ['status', 'payment_provider']  # status: success, failure
    )
    
    payment_refund_amount_total = Histogram(
        'payments_payment_refund_amount_total',
        'Refund amounts',
        ['currency'],
        buckets=(10, 30, 50, 100, 150, 300, 500, 1000)
    )
    
    # Payment Revenue Metrics
    payment_revenue_total = Counter(
        'payments_payment_revenue_total',
        'Total revenue from completed payments',
        ['currency']
    )
    
    payments_by_status = Gauge(
        'payments_payments_by_status',
        'Current number of payments by status',
        ['status']
    )
    
else:
    # Dummy metrics
    payment_creations_total = None
    payment_amount_total = None
    payment_status_transitions_total = None
    payment_processing_duration_seconds = None
    payment_provider_calls_total = None
    payment_provider_call_duration_seconds = None
    payment_failures_total = None
    payment_refunds_total = None
    payment_refund_amount_total = None
    payment_revenue_total = None
    payments_by_status = None


def track_payment_creation(currency: str, payment_provider: str, amount: float):
    """Track payment creation."""
    if payment_creations_total:
        payment_creations_total.labels(currency=currency, payment_provider=payment_provider or 'unknown').inc()
    if payment_amount_total:
        payment_amount_total.labels(currency=currency).observe(amount)


def track_payment_status_transition(from_status: str, to_status: str):
    """Track payment status transition."""
    if payment_status_transitions_total:
        payment_status_transitions_total.labels(from_status=from_status, to_status=to_status).inc()


def track_payment_processing(payment_provider: str, final_status: str, duration: float):
    """Track payment processing."""
    if payment_processing_duration_seconds:
        payment_processing_duration_seconds.labels(
            payment_provider=payment_provider or 'unknown',
            final_status=final_status
        ).observe(duration)


def track_payment_provider_call(provider: str, operation: str, status: str, duration: float):
    """Track payment provider API call."""
    if payment_provider_calls_total:
        payment_provider_calls_total.labels(provider=provider, operation=operation, status=status).inc()
    if payment_provider_call_duration_seconds:
        payment_provider_call_duration_seconds.labels(provider=provider, operation=operation).observe(duration)


def track_payment_failure(failure_reason: str, payment_provider: str):
    """Track payment failure."""
    if payment_failures_total:
        payment_failures_total.labels(
            failure_reason=failure_reason,
            payment_provider=payment_provider or 'unknown'
        ).inc()


def track_payment_refund(status: str, payment_provider: str, amount: float, currency: str):
    """Track payment refund."""
    if payment_refunds_total:
        payment_refunds_total.labels(status=status, payment_provider=payment_provider or 'unknown').inc()
    if payment_refund_amount_total:
        payment_refund_amount_total.labels(currency=currency).observe(amount)


def track_payment_revenue(currency: str, amount: float):
    """Track payment revenue."""
    if payment_revenue_total:
        payment_revenue_total.labels(currency=currency).inc(amount)


def update_payments_by_status(status: str, count: int):
    """Update payments by status gauge."""
    if payments_by_status:
        payments_by_status.labels(status=status).set(count)
