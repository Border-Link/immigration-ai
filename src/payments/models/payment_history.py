"""
Payment History Model

Tracks all payment events and status transitions for audit and debugging.
"""
import uuid
from django.db import models
from django.conf import settings
from payments.models.payment import Payment


class PaymentHistory(models.Model):
    """
    Payment history records for tracking all payment events.
    
    Stores status changes, gateway interactions, retries, and other events.
    """
    EVENT_TYPE_CHOICES = [
        ('created', 'Payment Created'),
        ('status_changed', 'Status Changed'),
        ('gateway_initiated', 'Gateway Initiated'),
        ('gateway_verified', 'Gateway Verified'),
        ('webhook_received', 'Webhook Received'),
        ('retry_attempted', 'Retry Attempted'),
        ('refund_initiated', 'Refund Initiated'),
        ('refund_completed', 'Refund Completed'),
        ('notification_sent', 'Notification Sent'),
        ('error_occurred', 'Error Occurred'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='history',
        db_index=True,
        help_text="The payment this history entry belongs to"
    )
    
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of event"
    )
    
    previous_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Previous payment status (if status changed)"
    )
    
    new_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="New payment status (if status changed)"
    )
    
    message = models.TextField(
        help_text="Event message or description"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event metadata (gateway response, error details, etc.)"
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this event (if applicable)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'payment_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]
        verbose_name_plural = 'Payment History'
    
    def __str__(self):
        return f"PaymentHistory {self.id} - {self.event_type} for Payment {self.payment.id}"
