"""
Admin Serializers for SourceDocument Management

Serializers for admin source document management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class SourceDocumentAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    data_source_id = serializers.UUIDField(required=False, allow_null=True)
    has_error = serializers.BooleanField(required=False, allow_null=True)
    http_status = serializers.IntegerField(required=False, allow_null=True)

    def to_internal_value(self, data):
        """Parse string dates to datetime objects and other types."""
        # Parse boolean and integer strings before calling super
        if 'has_error' in data and data.get('has_error') is not None:
            if isinstance(data['has_error'], str):
                data['has_error'] = data['has_error'].lower() == 'true'
        
        if 'http_status' in data and data.get('http_status'):
            if isinstance(data['http_status'], str):
                try:
                    data['http_status'] = int(data['http_status'])
                except (ValueError, TypeError):
                    pass
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


class BulkSourceDocumentOperationSerializer(serializers.Serializer):
    """Serializer for bulk source document operations."""
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
