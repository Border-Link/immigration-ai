"""
Admin Serializers for SourceDocument Management

Serializers for admin source document management operations.
"""
from rest_framework import serializers


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
