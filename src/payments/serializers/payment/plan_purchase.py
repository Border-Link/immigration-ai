from rest_framework import serializers
from payments.models.payment import Payment


class PlanPurchaseSerializer(serializers.Serializer):
    """
    Request serializer for purchasing a case-fee plan (pre-case payment).

    IMPORTANT: amount is NOT provided by the client; server derives it from settings.
    """

    plan = serializers.ChoiceField(
        choices=Payment.PLAN_CHOICES,
        required=True,
        help_text="Plan to purchase (basic/special/big).",
    )
    payment_provider = serializers.ChoiceField(
        choices=Payment.PAYMENT_PROVIDER_CHOICES,
        required=True,
        help_text="Payment gateway provider (stripe, paypal, or adyen).",
    )
    currency = serializers.ChoiceField(
        choices=Payment.SUPPORTED_CURRENCIES,
        required=False,
        default=Payment.DEFAULT_CURRENCY,
        help_text="Currency code (ISO 4217). Defaults to USD.",
    )

