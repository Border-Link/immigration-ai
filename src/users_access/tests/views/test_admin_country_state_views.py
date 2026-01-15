"""
Tests for admin country and state/province views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/auth"

@pytest.mark.django_db
class TestCountryActivateAPI:
    """Tests for CountryActivateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_activate_country(self, client, admin_user, test_country):
        """Test activating country."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/countries/{test_country.id}/activate/"
        data = {
            "is_active": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_deactivate_country(self, client, admin_user, test_country):
        """Test deactivating country."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/countries/{test_country.id}/activate/"
        data = {
            "is_active": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCountrySetJurisdictionAPI:
    """Tests for CountrySetJurisdictionAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_set_jurisdiction(self, client, admin_user, test_country):
        """Test setting country as jurisdiction."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/countries/{test_country.id}/set-jurisdiction/"
        data = {
            "is_jurisdiction": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestStateProvinceActivateAPI:
    """Tests for StateProvinceActivateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_activate_state(self, client, admin_user, test_state_province):
        """Test activating state/province."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/states/{test_state_province.id}/activate/"
        data = {
            "is_active": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_deactivate_state(self, client, admin_user, test_state_province):
        """Test deactivating state/province."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/states/{test_state_province.id}/activate/"
        data = {
            "is_active": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_activate_state_not_found(self, client, admin_user):
        """Test activating non-existent state."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/states/{uuid4()}/activate/"
        data = {"is_active": True}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_activate_state_requires_admin(self, client, test_user, test_state_province):
        """Test activating state requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/admin/states/{test_state_province.id}/activate/"
        data = {"is_active": True}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_activate_country_not_found(self, client, admin_user):
        """Test activating non-existent country."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/countries/{uuid4()}/activate/"
        data = {"is_active": True}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_activate_country_requires_admin(self, client, test_user, test_country):
        """Test activating country requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/admin/countries/{test_country.id}/activate/"
        data = {"is_active": True}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_set_jurisdiction_not_found(self, client, admin_user):
        """Test setting jurisdiction for non-existent country."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/countries/{uuid4()}/set-jurisdiction/"
        data = {"is_jurisdiction": True}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_set_jurisdiction_requires_admin(self, client, test_user, test_country):
        """Test setting jurisdiction requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/admin/countries/{test_country.id}/set-jurisdiction/"
        data = {"is_jurisdiction": True}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_set_jurisdiction_remove(self, client, admin_user, test_country):
        """Test removing jurisdiction status."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/countries/{test_country.id}/set-jurisdiction/"
        data = {"is_jurisdiction": False}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
