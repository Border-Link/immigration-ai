"""
Admin Serializers for DocumentDiff Management

Serializers for admin document diff management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class DocumentDiffAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    change_type = serializers.CharField(required=False, allow_null=True)


class BulkDocumentDiffOperationSerializer(serializers.Serializer):
    """Serializer for bulk document diff operations."""
    diff_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
