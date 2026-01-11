"""
Admin Serializers for VisaRequirement Management

Serializers for admin visa requirement management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class VisaRequirementAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating VisaRequirementAdminListAPI query parameters."""
    
    rule_version_id = serializers.UUIDField(required=False, allow_null=True)
    rule_type = serializers.CharField(required=False, allow_null=True, max_length=50)
    is_mandatory = serializers.BooleanField(required=False, allow_null=True)
    requirement_code = serializers.CharField(required=False, allow_null=True, max_length=100)
    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    jurisdiction = serializers.CharField(required=False, allow_null=True, max_length=10)
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


class VisaRequirementUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa requirement fields."""
    requirement_code = serializers.CharField(max_length=100, required=False)
    rule_type = serializers.ChoiceField(
        choices=[
            ('eligibility', 'Eligibility Requirement'),
            ('document', 'Document Requirement'),
            ('fee', 'Fee Information'),
            ('processing_time', 'Processing Time'),
            ('other', 'Other'),
        ],
        required=False
    )
    description = serializers.CharField(required=False, allow_blank=True)
    condition_expression = serializers.JSONField(required=False)
    is_mandatory = serializers.BooleanField(required=False)


class BulkVisaRequirementOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa requirement operations."""
    requirement_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'set_mandatory',
        'set_optional',
    ])
