from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from compliance.models.audit_log import AuditLog


class AuditLogListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating AuditLogListAPI query parameters."""
    
    level = serializers.CharField(required=False, allow_null=True, max_length=50)
    logger_name = serializers.CharField(required=False, allow_null=True, max_length=255)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for reading audit log data."""
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'level',
            'logger_name',
            'message',
            'timestamp',
            'pathname',
            'lineno',
            'func_name',
            'process',
            'thread',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuditLogListSerializer(serializers.ModelSerializer):
    """Serializer for listing audit logs."""
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'level',
            'logger_name',
            'message',
            'timestamp',
        ]

