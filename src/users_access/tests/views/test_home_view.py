"""
Tests for home view.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.views.home import HomeView


@pytest.mark.django_db
class TestHomeView:
    """Tests for HomeView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for home URL."""
        return "/"  # Adjust based on actual URL

    def test_home_view(self, client, url):
        """Test home view."""
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
