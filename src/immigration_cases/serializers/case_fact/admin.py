"""
Admin Serializers for CaseFact Management

Serializers for admin case fact management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from immigration_cases.models.case_fact import CaseFact


class CaseFactAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating CaseFactAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    fact_key = serializers.CharField(required=False, allow_null=True, max_length=255)
    source = serializers.ChoiceField(choices=CaseFact.SOURCE_CHOICES, required=False, allow_null=True)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    
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


class CaseFactAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to CaseFact."""
    
    class Meta:
        model = CaseFact
        fields = ['fact_value', 'source']


class BulkCaseFactOperationSerializer(serializers.Serializer):
    """Serializer for bulk case fact operations."""
    
    case_fact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'update_source',
    ])
    source = serializers.ChoiceField(
        choices=CaseFact.SOURCE_CHOICES,
        required=False,
        allow_null=True
    )
