"""
Tests for user account views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_service import UserService
from users_access.services.user_profile_service import UserProfileService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestUserAccountAPI:
    """Tests for UserAccountAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for account URL."""
        return f"{API_PREFIX}/users/account/"

    def test_get_user_account(self, client, url, test_user, user_profile_service):
        """Test getting user account."""
        user_profile_service.update_names(test_user, "John", "Doe")
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "profile" in response.data["data"]
        assert "account" in response.data["data"]
        assert "settings" in response.data["data"]
        assert "security" in response.data["data"]

    def test_get_user_account_unauthenticated(self, client, url):
        """Test getting user account without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
