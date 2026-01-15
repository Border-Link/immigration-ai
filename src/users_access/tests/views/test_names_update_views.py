"""
Tests for names update views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_profile_service import UserProfileService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestUserNamesUpdateAPI:
    """Tests for UserNamesUpdateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for names update URL."""
        return f"{API_PREFIX}/users/names/"

    def test_update_names_success(self, client, url, test_user):
        """Test successful names update."""
        client.force_authenticate(user=test_user)
        data = {
            "first_name": "Jane",
            "last_name": "Smith"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_update_names_unauthenticated(self, client, url):
        """Test updating names without authentication."""
        response = client.patch(url, {}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_names_invalid_data(self, client, url, test_user):
        """Test updating names with invalid data."""
        client.force_authenticate(user=test_user)
        data = {
            "first_name": "   ",
            "last_name": "Smith"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
