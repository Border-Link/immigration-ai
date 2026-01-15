"""
Tests for country views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.country_service import CountryService


@pytest.mark.django_db
class TestCountryCreateAPI:
    """Tests for CountryCreateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for country create URL."""
        return "/api/countries/"  # Adjust based on actual URL

    def test_create_country_as_admin(self, client, url, admin_user):
        """Test creating country as admin."""
        client.force_authenticate(user=admin_user)
        data = {
            "code": "CA",
            "name": "Canada"
        }
        response = client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_create_country_requires_auth(self, client, url):
        """Test creating country requires authentication."""
        data = {
            "code": "CA",
            "name": "Canada"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_country_duplicate(self, client, url, admin_user, country_service):
        """Test creating duplicate country."""
        country_service.create_country(code="US", name="United States")
        client.force_authenticate(user=admin_user)
        data = {
            "code": "US",
            "name": "USA"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCountryListAPI:
    """Tests for CountryListAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for country list URL."""
        return "/api/countries/"  # Adjust based on actual URL

    def test_list_countries(self, client, url, test_user):
        """Test listing countries."""
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_countries_unauthenticated(self, client, url):
        """Test listing countries without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCountryDetailAPI:
    """Tests for CountryDetailAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_get_country(self, client, test_user, test_country):
        """Test getting a country."""
        client.force_authenticate(user=test_user)
        url = f"/api/countries/{test_country.id}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_country_not_found(self, client, test_user):
        """Test getting non-existent country."""
        from uuid import uuid4
        client.force_authenticate(user=test_user)
        url = f"/api/countries/{uuid4()}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCountryJurisdictionsAPI:
    """Tests for CountryJurisdictionsAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for jurisdictions URL."""
        return "/api/countries/jurisdictions/"  # Adjust based on actual URL

    def test_get_jurisdictions(self, client, url, test_user, country_service):
        """Test getting jurisdictions."""
        country_service.create_country(code="CA", name="Canada", is_jurisdiction=True)
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCountrySearchAPI:
    """Tests for CountrySearchAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for search URL."""
        return "/api/countries/search/"  # Adjust based on actual URL

    def test_search_countries(self, client, url, test_user, country_service):
        """Test searching countries."""
        country_service.create_country(code="US", name="United States")
        client.force_authenticate(user=test_user)
        response = client.get(url, {"query": "United"})
        assert response.status_code == status.HTTP_200_OK

    def test_search_query_too_short(self, client, url, test_user):
        """Test search query too short."""
        client.force_authenticate(user=test_user)
        response = client.get(url, {"query": "U"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCountryUpdateAPI:
    """Tests for CountryUpdateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_update_country_as_admin(self, client, admin_user, test_country):
        """Test updating country as admin."""
        client.force_authenticate(user=admin_user)
        url = f"/api/countries/{test_country.id}/update/"
        data = {"name": "Updated Country Name"}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_update_country_requires_admin(self, client, test_user, test_country):
        """Test updating country requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"/api/countries/{test_country.id}/update/"
        data = {"name": "Updated Country Name"}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_country_not_found(self, client, admin_user):
        """Test updating non-existent country."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"/api/countries/{uuid4()}/update/"
        data = {"name": "Updated Country Name"}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_country_invalid_data(self, client, admin_user, test_country):
        """Test updating country with invalid data."""
        client.force_authenticate(user=admin_user)
        url = f"/api/countries/{test_country.id}/update/"
        data = {"code": ""}  # Invalid empty code
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCountryDeleteAPI:
    """Tests for CountryDeleteAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_delete_country_as_admin(self, client, admin_user, country_service):
        """Test deleting country as admin."""
        country = country_service.create_country(code="US", name="United States")
        client.force_authenticate(user=admin_user)
        url = f"/api/countries/{country.id}/delete/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_country_requires_admin(self, client, test_user, test_country):
        """Test deleting country requires admin permission."""
        client.force_authenticate(user=test_user)
        url = f"/api/countries/{test_country.id}/delete/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_country_not_found(self, client, admin_user):
        """Test deleting non-existent country."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"/api/countries/{uuid4()}/delete/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
