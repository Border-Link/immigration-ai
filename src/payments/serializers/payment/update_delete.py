from rest_framework import serializers
from payments.models.payment import Payment


class PaymentUpdateSerializer(serializers.Serializer):
    """Serializer for updating a payment."""
    
    status = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES,
        required=False
    )
    payment_provider = serializers.ChoiceField(
        choices=Payment.PAYMENT_PROVIDER_CHOICES,
        required=False,
        allow_null=True
    )
    provider_transaction_id = serializers.CharField(
        required=False,
        max_length=255,
        allow_null=True,
        allow_blank=True
    )
    version = serializers.IntegerField(
        required=False,
        help_text="Version number for optimistic locking"
    )

