from rest_framework import serializers
from users_access.models.notification import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'priority',
            'is_read',
            'read_at',
            'related_entity_type',
            'related_entity_id',
            'metadata',
            'created_at',
        ]
        read_only_fields = '__all__'


class NotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'priority',
            'is_read',
            'created_at',
        ]
        read_only_fields = '__all__'

