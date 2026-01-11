from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from compliance.models.audit_log import AuditLog


class AuditLogListQuerySerializer(serializers.Serializer):
    """Serializer for validating AuditLogListAPI query parameters."""
    
    level = serializers.CharField(required=False, allow_null=True, max_length=50)
    logger_name = serializers.CharField(required=False, allow_null=True, max_length=255)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    
    def validate(self, attrs):
        """Validate date ranges."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        return super().to_internal_value(data)


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

