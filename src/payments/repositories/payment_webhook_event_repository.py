"""
Payment Webhook Event Repository

Write-only data access layer for PaymentWebhookEvent.
"""
from typing import Optional, Dict, Any
from django.db import transaction
from payments.models.payment_webhook_event import PaymentWebhookEvent
from payments.models.payment import Payment


class PaymentWebhookEventRepository:
    """Repository for PaymentWebhookEvent write operations."""
    
    @staticmethod
    @transaction.atomic
    def create_webhook_event(
        payment: Payment,
        event_id: str,
        provider: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> PaymentWebhookEvent:
        """
        Create a new webhook event record.
        
        Args:
            payment: Payment instance
            event_id: Unique event ID from payment gateway
            provider: Payment provider name
            event_type: Event type from gateway
            payload: Original webhook payload
            
        Returns:
            Created PaymentWebhookEvent instance
            
        Raises:
            ValueError: If event_id already exists (idempotency violation)
        """
        # Check for duplicate event_id (idempotency)
        if PaymentWebhookEvent.objects.filter(event_id=event_id).exists():
            raise ValueError(f"Webhook event {event_id} already processed")
        
        webhook_event = PaymentWebhookEvent(
            payment=payment,
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            payload=payload
        )
        
        webhook_event.full_clean()
        webhook_event.save()
        
        return webhook_event
    
    @staticmethod
    @transaction.atomic
    def delete_webhook_event(webhook_event: PaymentWebhookEvent) -> None:
        """Delete a webhook event."""
        webhook_event.delete()
