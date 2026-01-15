"""
Tests for NotificationService.
All tests use services, not direct model access.
"""
import pytest
from uuid import uuid4
from users_access.services.notification_service import NotificationService


@pytest.mark.django_db
class TestNotificationService:
    """Tests for NotificationService."""

    def test_create_notification(self, notification_service, test_user):
        """Test creating notification."""
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        assert notification is not None
        assert notification.user == test_user

    def test_get_by_user(self, notification_service, test_user):
        """Test getting notifications by user."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        notifications = notification_service.get_by_user(str(test_user.id))
        assert notifications.count() >= 1

    def test_get_unread_by_user(self, notification_service, test_user):
        """Test getting unread notifications."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        notifications = notification_service.get_unread_by_user(str(test_user.id))
        assert notifications.count() >= 1

    def test_mark_as_read(self, notification_service, test_user):
        """Test marking notification as read."""
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        updated = notification_service.mark_as_read(str(notification.id))
        assert updated.is_read is True
        assert updated.read_at is not None

    def test_mark_all_as_read(self, notification_service, test_user):
        """Test marking all notifications as read."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test 1",
            message="Test message 1"
        )
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test 2",
            message="Test message 2"
        )
        result = notification_service.mark_all_as_read(str(test_user.id))
        assert result is True
        unread = notification_service.get_unread_by_user(str(test_user.id))
        assert unread.count() == 0

    def test_count_unread(self, notification_service, test_user):
        """Test counting unread notifications."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        count = notification_service.count_unread(str(test_user.id))
        assert count >= 1

    def test_get_by_id(self, notification_service, test_user):
        """Test getting notification by ID."""
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        found = notification_service.get_by_id(str(notification.id))
        assert found == notification

    def test_delete_notification(self, notification_service, test_user):
        """Test deleting notification."""
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        result = notification_service.delete_notification(str(notification.id))
        assert result is True
        found = notification_service.get_by_id(str(notification.id))
        assert found is None

    def test_create_notification_with_metadata(self, notification_service, test_user):
        """Test creating notification with metadata."""
        metadata = {"key": "value", "count": 5}
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message",
            metadata=metadata
        )
        assert notification.metadata == metadata

    def test_create_notification_invalid_user(self, notification_service):
        """Test creating notification with invalid user ID."""
        notification = notification_service.create_notification(
            user_id=str(uuid4()),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        assert notification is None

    def test_get_by_user_not_found(self, notification_service):
        """Test getting notifications for non-existent user."""
        notifications = notification_service.get_by_user(str(uuid4()))
        assert notifications.count() == 0

    def test_mark_as_read_not_found(self, notification_service):
        """Test marking non-existent notification as read."""
        result = notification_service.mark_as_read(str(uuid4()))
        assert result is None

    def test_mark_all_as_read_not_found(self, notification_service):
        """Test marking all as read for non-existent user."""
        result = notification_service.mark_all_as_read(str(uuid4()))
        assert result is True  # Should handle gracefully

    def test_count_unread_not_found(self, notification_service):
        """Test counting unread for non-existent user."""
        count = notification_service.count_unread(str(uuid4()))
        assert count == 0

    def test_get_by_id_not_found(self, notification_service):
        """Test getting non-existent notification by ID."""
        found = notification_service.get_by_id(str(uuid4()))
        assert found is None

    def test_delete_notification_not_found(self, notification_service):
        """Test deleting non-existent notification."""
        result = notification_service.delete_notification(str(uuid4()))
        assert result is False

    def test_create_notification_with_related_entity(self, notification_service, test_user):
        """Test creating notification with related entity."""
        related_id = str(uuid4())
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message",
            related_entity_type="case",
            related_entity_id=related_id
        )
        assert notification.related_entity_type == "case"
        assert str(notification.related_entity_id) == related_id
