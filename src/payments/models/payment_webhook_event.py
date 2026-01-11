"""
Payment Webhook Event Model

Tracks processed webhook events to prevent duplicate processing.
"""
import uuid
from django.db import models
from payments.models.payment import Payment


class PaymentWebhookEvent(models.Model):
    """
    Tracks processed webhook events for idempotency.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='webhook_events',
        db_index=True,
        help_text="The payment this webhook event belongs to"
    )
    
    event_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique event ID from payment gateway"
    )
    
    provider = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Payment provider (stripe, paypal, adyen)"
    )
    
    event_type = models.CharField(
        max_length=100,
        help_text="Event type from gateway"
    )
    
    payload = models.JSONField(
        default=dict,
        help_text="Original webhook payload"
    )
    
    processed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this webhook was processed"
    )
    
    class Meta:
        db_table = 'payment_webhook_events'
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['payment', '-processed_at']),
            models.Index(fields=['provider', 'event_id']),
        ]
        verbose_name_plural = 'Payment Webhook Events'
    
    def __str__(self):
        return f"WebhookEvent {self.event_id} for Payment {self.payment.id}"
