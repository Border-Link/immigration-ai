"""
Admin Serializers for EligibilityResult Management

Serializers for admin eligibility result management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating EligibilityResultAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    outcome = serializers.ChoiceField(choices=EligibilityResult.OUTCOME_CHOICES, required=False, allow_null=True)
    min_confidence = serializers.FloatField(required=False, allow_null=True, min_value=0.0, max_value=1.0)


class EligibilityResultAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating eligibility result in admin."""
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
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
