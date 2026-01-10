"""
Admin Serializers for DocumentChunk Management

Serializers for admin document chunk management operations.
"""
from rest_framework import serializers


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
