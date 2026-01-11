"""
Admin Serializers for DocumentVersion Management

Serializers for admin document version management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class DocumentVersionAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    source_document_id = serializers.UUIDField(required=False, allow_null=True)


class BulkDocumentVersionOperationSerializer(serializers.Serializer):
    """Serializer for bulk document version operations."""
    version_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
