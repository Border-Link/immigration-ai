import uuid
from django.db import models
from django.conf import settings
from immigration_cases.models.case import Case
from django.db.models import Q


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

    PAYMENT_PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('adyen', 'Adyen'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    PURPOSE_CHOICES = [
        ('case_fee', 'Case Fee'),
        ('reviewer_addon', 'Reviewer Add-on'),
        ('ai_calls_addon', 'AI Calls Add-on'),
    ]

    PLAN_CHOICES = [
        ('basic', 'Basic Plan'),
        ('special', 'Special Plan'),
        ('big', 'Big Plan'),
    ]

    # Supported currencies
    SUPPORTED_CURRENCIES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('JPY', 'Japanese Yen'),
        ('CHF', 'Swiss Franc'),
        ('NZD', 'New Zealand Dollar'),
        ('SGD', 'Singapore Dollar'),
        ('HKD', 'Hong Kong Dollar'),
        ('NGN', 'Nigerian Naira'),
        ('AED', 'UAE Dirham'),
        ('ZAR', 'South African Rand'),
        ('INR', 'Indian Rupee')
    ]
    
    DEFAULT_CURRENCY = 'USD'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True,
        help_text="The user this payment belongs to (required for pre-case payments)",
    )

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True,
        null=True,
        blank=True,
        help_text="The case this payment belongs to (nullable for pre-case payments)"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    
    currency = models.CharField(
        max_length=3,
        default=DEFAULT_CURRENCY,
        choices=SUPPORTED_CURRENCIES,
        db_index=True,
        help_text="Currency code (ISO 4217)"
    )
    
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts for failed payments"
    )
    
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )
    
    last_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last retry attempt"
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

    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        default='case_fee',
        db_index=True,
        help_text="What this payment is for (case fee vs add-ons like reviewer)"
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Plan purchased with the case fee payment (basic/special/big). Only applicable when purpose=case_fee.",
    )
    
    provider_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Transaction ID from payment provider"
    )
    
    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")
    
    # Soft delete fields
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Whether this payment is soft deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this payment was deleted")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['case', 'purpose', 'status']),
            models.Index(fields=['case', 'purpose', 'plan', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                name="payments_case_fee_requires_plan",
                condition=~Q(purpose="case_fee") | (~Q(plan__isnull=True) & ~Q(plan="")),
            ),
        ]
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} ({self.status})"

