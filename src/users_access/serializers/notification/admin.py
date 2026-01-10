"""
Admin Serializers for Notification Management

Serializers for admin notification management operations.
"""
from rest_framework import serializers
from users_access.models.notification import Notification


class NotificationCreateSerializer(serializers.Serializer):
    """Serializer for creating a notification."""
    user_id = serializers.UUIDField(required=True)
    notification_type = serializers.ChoiceField(choices=Notification.TYPE_CHOICES, required=True)
    title = serializers.CharField(required=True, max_length=255)
    message = serializers.CharField(required=True)
    priority = serializers.ChoiceField(choices=Notification.PRIORITY_CHOICES, default='medium')
    related_entity_type = serializers.CharField(required=False, allow_null=True, max_length=50)
    related_entity_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)


class BulkNotificationCreateSerializer(serializers.Serializer):
    """Serializer for creating bulk notifications."""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    notification_type = serializers.ChoiceField(choices=Notification.TYPE_CHOICES, required=True)
    title = serializers.CharField(required=True, max_length=255)
    message = serializers.CharField(required=True)
    priority = serializers.ChoiceField(choices=Notification.PRIORITY_CHOICES, default='medium')
    related_entity_type = serializers.CharField(required=False, allow_null=True, max_length=50)
    related_entity_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)
