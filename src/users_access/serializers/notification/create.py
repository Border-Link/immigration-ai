from rest_framework import serializers


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""
    notification_id = serializers.UUIDField(required=False)
    mark_all = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        """Ensure either notification_id or mark_all is provided."""
        if not data.get('notification_id') and not data.get('mark_all'):
            raise serializers.ValidationError("Either 'notification_id' or 'mark_all' must be provided.")
        return data

