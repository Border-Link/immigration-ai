"""
Admin Serializers for VisaDocumentRequirement Management

Serializers for admin visa document requirement management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class VisaDocumentRequirementAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating VisaDocumentRequirementAdminListAPI query parameters."""
    
    visa_requirement_id = serializers.UUIDField(required=False, allow_null=True)
    document_type_id = serializers.UUIDField(required=False, allow_null=True)
    mandatory = serializers.BooleanField(required=False, allow_null=True)
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


class VisaDocumentRequirementUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa document requirement fields."""
    mandatory = serializers.BooleanField(required=False)
    conditional_logic = serializers.JSONField(required=False, allow_null=True)


class BulkVisaDocumentRequirementOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa document requirement operations."""
    document_requirement_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'set_mandatory',
        'set_optional',
        'delete',
    ])
