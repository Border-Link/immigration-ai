from users_access.models.notification import Notification
from django.conf import settings


class NotificationSelector:
    """Selector for Notification read operations."""

    @staticmethod
    def get_all():
        """Get all notifications."""
        return Notification.objects.select_related('user').all().order_by('-created_at')

    @staticmethod
    def get_by_user(user):
        """Get notifications for a specific user."""
        return Notification.objects.select_related('user').filter(user=user).order_by('-created_at')

    @staticmethod
    def get_unread_by_user(user):
        """Get unread notifications for a specific user."""
        return Notification.objects.select_related('user').filter(
            user=user,
            is_read=False
        ).order_by('-created_at')

    @staticmethod
    def get_by_type(user, notification_type: str):
        """Get notifications by type for a user."""
        return Notification.objects.select_related('user').filter(
            user=user,
            notification_type=notification_type
        ).order_by('-created_at')

    @staticmethod
    def get_by_related_entity(related_entity_type: str, related_entity_id: str):
        """Get notifications by related entity."""
        return Notification.objects.select_related('user').filter(
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        ).order_by('-created_at')

    @staticmethod
    def get_by_id(notification_id):
        """Get notification by ID."""
        return Notification.objects.select_related('user').get(id=notification_id)

    @staticmethod
    def count_unread_by_user(user):
        """Count unread notifications for a user."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return Notification.objects.none()
