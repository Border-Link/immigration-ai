"""
Admin Serializers for DocumentType Management

Serializers for admin document type management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class DocumentTypeAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating DocumentTypeAdminListAPI query parameters."""
    
    is_active = serializers.BooleanField(required=False, allow_null=True)
    code = serializers.CharField(required=False, allow_null=True, max_length=50)
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


class DocumentTypeActivateSerializer(serializers.Serializer):
    """Serializer for activating/deactivating a document type."""
    is_active = serializers.BooleanField(required=True)


class BulkDocumentTypeOperationSerializer(serializers.Serializer):
    """Serializer for bulk document type operations."""
    document_type_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'activate',
        'deactivate',
        'delete',
    ])
