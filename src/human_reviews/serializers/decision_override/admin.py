"""
Admin Serializers for DecisionOverride Management

Serializers for admin decision override management operations.
"""
from rest_framework import serializers


class DecisionOverrideAdminUpdateSerializer(serializers.Serializer):
    """Serializer for admin decision override updates."""
    overridden_outcome = serializers.ChoiceField(
        choices=['eligible', 'not_eligible', 'requires_review'],
        required=False
    )
    reason = serializers.CharField(required=False)


class BulkDecisionOverrideOperationSerializer(serializers.Serializer):
    """Serializer for bulk decision override operations."""
    decision_override_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
