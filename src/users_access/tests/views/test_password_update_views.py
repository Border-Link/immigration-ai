"""
Tests for password update views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_service import UserService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestUserPasswordUpdateAPI:
    """Tests for UserPasswordUpdateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for password update URL."""
        return f"{API_PREFIX}/users/password/update/"

    def test_update_password_success(self, client, url, verified_user):
        """Test successful password update."""
        client.force_authenticate(user=verified_user)
        data = {
            "old_password": "testpass123",
            "password": "NewPass123!@#"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_update_password_invalid_old_password(self, client, url, verified_user):
        """Test password update with invalid old password."""
        client.force_authenticate(user=verified_user)
        data = {
            "old_password": "wrongpassword",
            "password": "NewPass123!@#"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_password_unauthenticated(self, client, url):
        """Test updating password without authentication."""
        response = client.patch(url, {}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
