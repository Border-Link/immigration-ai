"""
Admin Serializers for DecisionOverride Management

Serializers for admin decision override management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class DecisionOverrideAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    case_id = serializers.UUIDField(required=False, allow_null=True)
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    original_result_id = serializers.UUIDField(required=False, allow_null=True)
    overridden_outcome = serializers.ChoiceField(
        choices=['eligible', 'not_eligible', 'requires_review'],
        required=False,
        allow_null=True
    )


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
