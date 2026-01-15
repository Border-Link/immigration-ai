"""
Tests for user status views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_service import UserService


@pytest.mark.django_db
class TestUserStatusAPI:
    """Tests for UserStatusAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for user status URL."""
        return "/api/users/status/"  # Adjust based on actual URL

    def test_get_user_status(self, client, url, test_user):
        """Test getting user status."""
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["email"] == test_user.email

    def test_get_user_status_unauthenticated(self, client, url):
        """Test getting user status without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
