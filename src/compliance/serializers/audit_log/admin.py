"""
Admin serializers for AuditLog operations.
"""
from rest_framework import serializers
from compliance.models.audit_log import AuditLog


class AuditLogAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing audit logs in admin."""
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'level',
            'logger_name',
            'message',
            'timestamp',
            'created_at',
        ]
        read_only_fields = '__all__'


class AuditLogAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed audit log view in admin."""
    
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
        read_only_fields = '__all__'


class BulkAuditLogOperationSerializer(serializers.Serializer):
    """Serializer for bulk audit log operations."""
    log_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
