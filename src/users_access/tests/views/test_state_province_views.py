"""
Tests for state/province views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.state_province_service import StateProvinceService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestStateProvinceCreateAPI:
    """Tests for StateProvinceCreateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for state create URL."""
        return f"{API_PREFIX}/states/"

    def test_create_state_as_admin(self, client, url, admin_user, test_country):
        """Test creating state as admin."""
        client.force_authenticate(user=admin_user)
        data = {
            "country_id": str(test_country.id),
            "code": "NY",
            "name": "New York"
        }
        response = client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_create_state_requires_auth(self, client, url, test_country):
        """Test creating state requires authentication."""
        data = {
            "country_id": str(test_country.id),
            "code": "NY",
            "name": "New York"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestStateProvinceReadAPI:
    """Tests for StateProvince read views."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_list_states_by_country(self, client, test_user, test_country, state_province_service):
        """Test listing states by country."""
        state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="NY",
            name="New York"
        )
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/states/country/{test_country.id}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_state_detail(self, client, test_user, test_state_province):
        """Test getting state detail."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/states/{test_state_province.id}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_state_not_found(self, client, test_user):
        """Test getting non-existent state."""
        from uuid import uuid4
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/states/{uuid4()}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestStateProvinceUpdateAPI:
    """Tests for StateProvinceUpdateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_update_state_as_admin(self, client, admin_user, test_state_province):
        """Test updating state as admin."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/states/{test_state_province.id}/update/"
        data = {"name": "Updated State Name"}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_update_state_requires_admin(self, client, test_user, test_state_province):
        """Test updating state requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/states/{test_state_province.id}/update/"
        data = {"name": "Updated State Name"}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_state_not_found(self, client, admin_user):
        """Test updating non-existent state."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/states/{uuid4()}/update/"
        data = {"name": "Updated State Name"}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_state_invalid_data(self, client, admin_user, test_state_province):
        """Test updating state with invalid data."""
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/states/{test_state_province.id}/update/"
        data = {"code": ""}  # Invalid empty code
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestStateProvinceDeleteAPI:
    """Tests for StateProvinceDeleteAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_delete_state_as_admin(self, client, admin_user, state_province_service, test_country):
        """Test deleting state as admin."""
        state = state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="NY",
            name="New York"
        )
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/states/{state.id}/delete/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_state_requires_admin(self, client, test_user, test_state_province):
        """Test deleting state requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/states/{test_state_province.id}/delete/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_state_not_found(self, client, admin_user):
        """Test deleting non-existent state."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/states/{uuid4()}/delete/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
