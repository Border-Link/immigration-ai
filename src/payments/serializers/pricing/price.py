from rest_framework import serializers
from payments.models.pricing import PricingItemPrice
from payments.models.payment import Payment


class PricingItemPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingItemPrice
        fields = ["id", "pricing_item", "currency", "amount", "created_at", "updated_at"]
        read_only_fields = ["id", "pricing_item", "created_at", "updated_at"]


class PricingItemPriceUpsertSerializer(serializers.Serializer):
    currency = serializers.ChoiceField(choices=Payment.SUPPORTED_CURRENCIES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

