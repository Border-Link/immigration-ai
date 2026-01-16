from rest_framework import serializers
from payments.models.pricing import PricingItem


class PricingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingItem
        fields = [
            "id",
            "kind",
            "code",
            "name",
            "description",
            "is_active",
            "includes_ai_calls",
            "includes_human_review",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PricingItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingItem
        fields = [
            "kind",
            "code",
            "name",
            "description",
            "is_active",
            "includes_ai_calls",
            "includes_human_review",
        ]


class PricingItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingItem
        fields = [
            "name",
            "description",
            "is_active",
            "includes_ai_calls",
            "includes_human_review",
        ]
