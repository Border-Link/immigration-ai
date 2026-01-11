"""
Admin Serializers for DocumentChunk Management

Serializers for admin document chunk management operations.
"""
from rest_framework import serializers


class DocumentChunkAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating query parameters in admin list view."""
    document_version_id = serializers.UUIDField(required=False, allow_null=True)
    has_embedding = serializers.BooleanField(required=False, allow_null=True)

    def to_internal_value(self, data):
        """Parse boolean string to boolean."""
        if 'has_embedding' in data and data['has_embedding'] is not None:
            if isinstance(data['has_embedding'], str):
                data['has_embedding'] = data['has_embedding'].lower() == 'true'
        
        return super().to_internal_value(data)


class BulkDocumentChunkOperationSerializer(serializers.Serializer):
    """Serializer for bulk document chunk operations."""
    chunk_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        're_embed',
    ])
