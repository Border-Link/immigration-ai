"""
Admin Serializers for DocumentType Management

Serializers for admin document type management operations.
"""
from rest_framework import serializers


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
