"""
Admin Serializers for AuditLog Management

Serializers for admin audit log management operations.
"""
from rest_framework import serializers


class AuditLogListSerializer(serializers.Serializer):
    """Serializer for audit log list."""
    id = serializers.UUIDField()
    action = serializers.CharField()
    status = serializers.CharField()
    error_type = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class AuditLogDetailSerializer(serializers.Serializer):
    """Serializer for audit log detail."""
    id = serializers.UUIDField()
    document_version_id = serializers.UUIDField(allow_null=True)
    action = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField(allow_null=True)
    error_type = serializers.CharField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)
    user_id = serializers.UUIDField(allow_null=True)
    user_email = serializers.EmailField(allow_null=True)
    metadata = serializers.JSONField(allow_null=True)
    ip_address = serializers.IPAddressField(allow_null=True)
    user_agent = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class AuditLogAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    action = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
    error_type = serializers.CharField(required=False, allow_null=True)
    user_id = serializers.UUIDField(required=False, allow_null=True)
    document_version_id = serializers.UUIDField(required=False, allow_null=True)
