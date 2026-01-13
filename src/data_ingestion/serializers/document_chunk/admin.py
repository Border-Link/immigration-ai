"""
Admin Serializers for DocumentChunk Management

Serializers for admin document chunk management operations.
"""
from rest_framework import serializers


class DocumentChunkAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating query parameters in admin list view."""
    document_version_id = serializers.UUIDField(required=False, allow_null=True)
    has_embedding = serializers.BooleanField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=200, default=50)
    include_text_preview = serializers.BooleanField(required=False, default=False)

    def to_internal_value(self, data):
        """Parse boolean string to boolean and handle pagination."""
        if 'has_embedding' in data and data['has_embedding'] is not None:
            if isinstance(data['has_embedding'], str):
                data['has_embedding'] = data['has_embedding'].lower() == 'true'
        
        if 'include_text_preview' in data and isinstance(data['include_text_preview'], str):
            data['include_text_preview'] = data['include_text_preview'].lower() == 'true'
        
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
    model = serializers.CharField(
        required=False,
        default='text-embedding-ada-002',
        help_text="Embedding model to use for re_embed operation (default: text-embedding-ada-002)"
    )