"""
Refund Serializers

Serializers for payment refund operations.
"""
from rest_framework import serializers
from decimal import Decimal


class PaymentRefundSerializer(serializers.Serializer):
    """Serializer for processing a payment refund."""
    
    amount = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Refund amount (optional, full refund if not specified)"
    )
    reason = serializers.CharField(
        required=False,
        max_length=500,
        allow_blank=True,
        help_text="Reason for refund"
    )
