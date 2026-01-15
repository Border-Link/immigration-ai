"""
Tests for notification views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.notification_service import NotificationService


@pytest.mark.django_db
class TestNotificationListAPI:
    """Tests for NotificationListAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for notification list URL."""
        return "/api/notifications/"  # Adjust based on actual URL

    def test_list_notifications(self, client, url, test_user, notification_service):
        """Test listing notifications."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_unread_notifications(self, client, url, test_user, notification_service):
        """Test listing unread notifications."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=test_user)
        response = client.get(url, {"unread_only": "true"})
        assert response.status_code == status.HTTP_200_OK

    def test_list_notifications_unauthenticated(self, client, url):
        """Test listing notifications without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestNotificationDetailAPI:
    """Tests for NotificationDetailAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_get_notification(self, client, test_user, notification_service):
        """Test getting a notification."""
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=test_user)
        url = f"/api/notifications/{notification.id}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_notification_not_found(self, client, test_user):
        """Test getting non-existent notification."""
        from uuid import uuid4
        client.force_authenticate(user=test_user)
        url = f"/api/notifications/{uuid4()}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestNotificationMarkReadAPI:
    """Tests for NotificationMarkReadAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for mark read URL."""
        return "/api/notifications/mark-read/"  # Adjust based on actual URL

    def test_mark_notification_read(self, client, url, test_user, notification_service):
        """Test marking notification as read."""
        notification = notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=test_user)
        data = {
            "notification_id": str(notification.id)
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_mark_all_notifications_read(self, client, url, test_user, notification_service):
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
        client.force_authenticate(user=test_user)
        data = {
            "mark_all": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestNotificationUnreadCountAPI:
    """Tests for NotificationUnreadCountAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for unread count URL."""
        return "/api/notifications/unread-count/"  # Adjust based on actual URL

    def test_get_unread_count(self, client, url, test_user, notification_service):
        """Test getting unread count."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["unread_count"] >= 1
