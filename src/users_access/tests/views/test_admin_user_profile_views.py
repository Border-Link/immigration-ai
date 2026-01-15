"""
Tests for admin user profile views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_profile_service import UserProfileService


@pytest.mark.django_db
class TestUserProfileAdminListAPI:
    """Tests for UserProfileAdminListAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for admin profiles list URL."""
        return "/api/admin/user-profiles/"  # Adjust based on actual URL

    def test_list_profiles_as_admin(self, client, url, admin_user, user_profile_service, test_user):
        """Test listing profiles as admin."""
        user_profile_service.update_names(test_user, "John", "Doe")
        client.force_authenticate(user=admin_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_profiles_with_filters(self, client, url, admin_user, user_profile_service, test_user, test_country):
        """Test listing profiles with filters."""
        user_profile_service.update_nationality(test_user, "US")
        client.force_authenticate(user=admin_user)
        response = client.get(url, {"nationality": "US"})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserProfileAdminDetailAPI:
    """Tests for UserProfileAdminDetailAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_get_profile_detail(self, client, admin_user, test_user):
        """Test getting profile detail."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/user-profiles/{test_user.id}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserProfileAdminUpdateAPI:
    """Tests for UserProfileAdminUpdateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_update_profile(self, client, admin_user, test_user):
        """Test updating profile."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/user-profiles/{test_user.id}/"
        data = {
            "first_name": "Jane",
            "last_name": "Smith"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
