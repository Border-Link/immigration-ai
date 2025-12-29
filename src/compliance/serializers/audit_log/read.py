from rest_framework import serializers
from compliance.models.audit_log import AuditLog


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

