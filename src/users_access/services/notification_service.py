import logging
from typing import Optional
from django.conf import settings
from users_access.models.notification import Notification
from users_access.repositories.notification_repository import NotificationRepository
from users_access.selectors.notification_selector import NotificationSelector
from users_access.selectors.user_selector import UserSelector

logger = logging.getLogger('django')


class NotificationService:
    """Service for Notification business logic."""

    @staticmethod
    def create_notification(user_id: str, notification_type: str, title: str, message: str,
                           priority: str = 'medium', related_entity_type: str = None,
                           related_entity_id: str = None, metadata: dict = None) -> Optional[Notification]:
        """Create a new notification."""
        try:
            user = UserSelector.get_by_id(user_id)
            return NotificationRepository.create_notification(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None

    @staticmethod
    def get_by_user(user_id: str):
        """Get notifications for a user."""
        try:
            user = UserSelector.get_by_id(user_id)
            return NotificationSelector.get_by_user(user)
        except Exception as e:
            logger.error(f"Error fetching notifications for user {user_id}: {e}")
            return NotificationSelector.get_none()

    @staticmethod
    def get_unread_by_user(user_id: str):
        """Get unread notifications for a user."""
        try:
            user = UserSelector.get_by_id(user_id)
            return NotificationSelector.get_unread_by_user(user)
        except Exception as e:
            logger.error(f"Error fetching unread notifications for user {user_id}: {e}")
            return NotificationSelector.get_none()

    @staticmethod
    def mark_as_read(notification_id: str) -> Optional[Notification]:
        """Mark a notification as read."""
        try:
            notification = NotificationSelector.get_by_id(notification_id)
            return NotificationRepository.mark_as_read(notification)
        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return None

    @staticmethod
    def mark_all_as_read(user_id: str) -> bool:
        """Mark all notifications for a user as read."""
        try:
            user = UserSelector.get_by_id(user_id)
            NotificationRepository.mark_all_as_read(user)
            return True
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {e}")
            return False

    @staticmethod
    def count_unread(user_id: str) -> int:
        """Count unread notifications for a user."""
        try:
            user = UserSelector.get_by_id(user_id)
            return NotificationSelector.count_unread_by_user(user)
        except Exception as e:
            logger.error(f"Error counting unread notifications for user {user_id}: {e}")
            return 0

    @staticmethod
    def get_by_id(notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        try:
            return NotificationSelector.get_by_id(notification_id)
        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching notification {notification_id}: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all notifications."""
        try:
            return NotificationSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all notifications: {e}")
            return NotificationSelector.get_none()

    @staticmethod
    def delete_notification(notification_id: str) -> bool:
        """Delete a notification."""
        try:
            notification = NotificationSelector.get_by_id(notification_id)
            if not notification:
                logger.error(f"Notification {notification_id} not found")
                return False
            NotificationRepository.delete_notification(notification)
            return True
        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}")
            return False
