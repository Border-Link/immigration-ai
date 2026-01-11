"""
Payment Webhook Event Selector

Read-only data access layer for PaymentWebhookEvent.
"""
from typing import Optional
from django.db.models import QuerySet
from payments.models.payment_webhook_event import PaymentWebhookEvent
from payments.models.payment import Payment


class PaymentWebhookEventSelector:
    """Selector for PaymentWebhookEvent read operations."""
    
    @staticmethod
    def get_all() -> QuerySet[PaymentWebhookEvent]:
        """Get all webhook events."""
        return PaymentWebhookEvent.objects.all().select_related('payment', 'payment__case')
    
    @staticmethod
    def get_by_id(event_id: str) -> Optional[PaymentWebhookEvent]:
        """Get webhook event by ID."""
        try:
            return PaymentWebhookEvent.objects.select_related('payment', 'payment__case').get(id=event_id)
        except PaymentWebhookEvent.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_event_id(event_id: str) -> Optional[PaymentWebhookEvent]:
        """Get webhook event by gateway event ID (for idempotency checks)."""
        try:
            return PaymentWebhookEvent.objects.select_related('payment', 'payment__case').get(event_id=event_id)
        except PaymentWebhookEvent.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_payment(payment: Payment) -> QuerySet[PaymentWebhookEvent]:
        """Get all webhook events for a payment."""
        return PaymentWebhookEvent.objects.filter(payment=payment).order_by('-processed_at')
    
    @staticmethod
    def get_by_provider(provider: str) -> QuerySet[PaymentWebhookEvent]:
        """Get all webhook events for a provider."""
        return PaymentWebhookEvent.objects.filter(provider=provider).select_related('payment', 'payment__case').order_by('-processed_at')
    
    @staticmethod
    def get_by_filters(
        payment_id: str = None,
        provider: str = None,
        event_type: str = None,
        event_id: str = None
    ) -> QuerySet[PaymentWebhookEvent]:
        """Get webhook events with advanced filtering."""
        queryset = PaymentWebhookEvent.objects.all().select_related('payment', 'payment__case')
        
        if payment_id:
            queryset = queryset.filter(payment_id=payment_id)
        
        if provider:
            queryset = queryset.filter(provider=provider)
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset.order_by('-processed_at')
