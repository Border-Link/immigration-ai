"""
Tests for admin notification views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.notification_service import NotificationService


@pytest.mark.django_db
class TestNotificationAdminListAPI:
    """Tests for NotificationAdminListAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for admin notifications list URL."""
        return "/api/admin/notifications/"  # Adjust based on actual URL

    def test_list_notifications_as_admin(self, client, url, admin_user, notification_service, test_user):
        """Test listing notifications as admin."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=admin_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_notifications_with_filters(self, client, url, admin_user, notification_service, test_user):
        """Test listing notifications with filters."""
        notification_service.create_notification(
            user_id=str(test_user.id),
            notification_type="case_status_update",
            title="Test",
            message="Test message"
        )
        client.force_authenticate(user=admin_user)
        response = client.get(url, {"notification_type": "case_status_update"})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestNotificationAdminCreateAPI:
    """Tests for NotificationAdminCreateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for admin create notification URL."""
        return "/api/admin/notifications/"  # Adjust based on actual URL

    def test_create_notification(self, client, url, admin_user, test_user):
        """Test creating notification as admin."""
        client.force_authenticate(user=admin_user)
        data = {
            "user_id": str(test_user.id),
            "notification_type": "case_status_update",
            "title": "Test",
            "message": "Test message"
        }
        response = client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]


@pytest.mark.django_db
class TestNotificationAdminBulkCreateAPI:
    """Tests for NotificationAdminBulkCreateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for bulk create URL."""
        return "/api/admin/notifications/bulk/"  # Adjust based on actual URL

    def test_bulk_create_notifications(self, client, url, admin_user, user_service):
        """Test bulk creating notifications."""
        user1 = user_service.create_user("user1@example.com", "pass123")
        user2 = user_service.create_user("user2@example.com", "pass123")
        client.force_authenticate(user=admin_user)
        data = {
            "user_ids": [str(user1.id), str(user2.id)],
            "notification_type": "case_status_update",
            "title": "Test",
            "message": "Test message"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
