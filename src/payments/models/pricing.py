import uuid
from django.db import models
from payments.models.payment import Payment


class PricingItem(models.Model):
    """
    Admin-configurable pricing + entitlements for plans and add-ons.

    - kind=plan: represents per-case plan purchased with purpose=case_fee and plan=<code>
    - kind=addon: represents add-on purchases (e.g., reviewer_addon) purchased with purpose=<code>
    """

    KIND_CHOICES = [
        ("plan", "Plan"),
        ("addon", "Add-on"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    kind = models.CharField(max_length=20, choices=KIND_CHOICES, db_index=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True, db_index=True)

    # Entitlements (evaluated at runtime by PaymentValidator)
    includes_ai_calls = models.BooleanField(default=False)
    includes_human_review = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pricing_items"
        ordering = ["kind", "code"]
        indexes = [
            models.Index(fields=["kind", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind}:{self.code}"


class PricingItemPrice(models.Model):
    """Currency-specific price for a PricingItem."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    pricing_item = models.ForeignKey(
        PricingItem,
        on_delete=models.CASCADE,
        related_name="prices",
        db_index=True,
    )

    currency = models.CharField(
        max_length=3,
        choices=Payment.SUPPORTED_CURRENCIES,
        db_index=True,
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pricing_item_prices"
        ordering = ["pricing_item", "currency"]
        constraints = [
            models.UniqueConstraint(
                fields=["pricing_item", "currency"],
                name="uniq_pricing_item_currency",
            )
        ]
        indexes = [
            models.Index(fields=["currency", "amount"]),
        ]

    def __str__(self) -> str:
        return f"{self.pricing_item} {self.currency} {self.amount}"

