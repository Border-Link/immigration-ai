import uuid
from django.db import models
from immigration_cases.models.case import Case


class Payment(models.Model):
    """
    Payment records for immigration cases.
    Tracks payment status and provider information.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    CURRENCY_CHOICES = [
        ('GBP', 'British Pound'),
        ('USD', 'US Dollar'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
    ]

    PAYMENT_PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True,
        help_text="The case this payment belongs to"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='GBP',
        help_text="Currency code"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Payment status"
    )
    
    payment_provider = models.CharField(
        max_length=50,
        choices=PAYMENT_PROVIDER_CHOICES,
        null=True,
        blank=True,
        help_text="Payment provider used"
    )
    
    provider_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Transaction ID from payment provider"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} ({self.status})"

