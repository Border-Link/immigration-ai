from rest_framework import serializers
from payments.models.payment import Payment


class ReviewerAddonPurchaseSerializer(serializers.Serializer):
    """
    Request serializer for purchasing the 'Immigration Reviewer' add-on for an existing case.

    IMPORTANT: amount is NOT provided by the client; server derives it from settings.
    """

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

