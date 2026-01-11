"""
Admin Serializers for DocumentType Management

Serializers for admin document type management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import (
    BaseAdminListQuerySerializer,
    ActivateSerializer as BaseActivateSerializer
)


class DocumentTypeAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating DocumentTypeAdminListAPI query parameters."""
    
    is_active = serializers.BooleanField(required=False, allow_null=True)
    code = serializers.CharField(required=False, allow_null=True, max_length=50)


class DocumentTypeActivateSerializer(BaseActivateSerializer):
    """Serializer for activating/deactivating a document type."""
    pass


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
