"""
Admin Serializers for EligibilityResult Management

Serializers for admin eligibility result management operations.
"""
from rest_framework import serializers
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating eligibility result in admin."""
    outcome = serializers.ChoiceField(choices=EligibilityResult.OUTCOME_CHOICES, required=False)
    confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    reasoning_summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    missing_facts = serializers.JSONField(required=False, allow_null=True)


class BulkEligibilityResultOperationSerializer(serializers.Serializer):
    """Serializer for bulk eligibility result operations."""
    result_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'update_outcome',
    ])
    # For update_outcome operation
    outcome = serializers.ChoiceField(choices=EligibilityResult.OUTCOME_CHOICES, required=False)
    confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    reasoning_summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)
