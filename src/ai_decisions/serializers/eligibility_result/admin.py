"""
Admin Serializers for EligibilityResult Management

Serializers for admin eligibility result management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating EligibilityResultAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    outcome = serializers.ChoiceField(choices=EligibilityResult.OUTCOME_CHOICES, required=False, allow_null=True)
    min_confidence = serializers.FloatField(required=False, allow_null=True, min_value=0.0, max_value=1.0)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    
    def validate(self, attrs):
        """Validate date ranges."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        return super().to_internal_value(data)


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
