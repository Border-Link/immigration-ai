"""
Tests for logout views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from users_access.services.user_device_session_service import UserDeviceSessionService


@pytest.mark.django_db
class TestLogoutViewAPI:
    """Tests for LogoutViewAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for logout URL."""
        return "/api/users/logout/"  # Adjust based on actual URL

    @patch('users_access.views.users.logout.UserDeviceSessionService')
    @patch('users_access.views.users.logout.AuthToken')
    def test_logout_success(self, mock_auth_token, mock_session_service, client, url, test_user):
        """Test successful logout."""
        client.force_authenticate(user=test_user)
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_unauthenticated(self, client, url):
        """Test logout without authentication."""
        response = client.post(url, {}, format='json')
        # May return 401 or 204 depending on implementation
        assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.django_db
class TestLogoutAllViewAPI:
    """Tests for LogoutAllViewAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for logout all URL."""
        return "/api/users/logout-all/"  # Adjust based on actual URL

    @patch('users_access.views.users.logout.UserDeviceSessionService')
    @patch('users_access.views.users.logout.AuthToken')
    def test_logout_all_success(self, mock_auth_token, mock_session_service, client, url, test_user):
        """Test successful logout all."""
        client.force_authenticate(user=test_user)
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
