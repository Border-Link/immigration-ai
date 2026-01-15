"""
Tests for avatar views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import MagicMock, patch
from users_access.services.user_profile_service import UserProfileService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestUserAvatarAPI:
    """Tests for UserAvatarAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for avatar URL."""
        return f"{API_PREFIX}/users/avatar/"

    @patch('users_access.serializers.users.add_avatar.img_processor')
    def test_update_avatar_success(self, mock_img_processor, client, url, test_user):
        """Test successful avatar update."""
        client.force_authenticate(user=test_user)
        mock_processor = MagicMock()
        mock_processed = MagicMock()
        mock_processor.process.return_value = mock_processed
        mock_img_processor.ImageProcessor.return_value = mock_processor
        
        mock_file = MagicMock()
        data = {
            "avatar": mock_file
        }
        response = client.patch(url, data, format='multipart')
        assert response.status_code == status.HTTP_200_OK

    def test_update_avatar_unauthenticated(self, client, url):
        """Test updating avatar without authentication."""
        response = client.patch(url, {}, format='multipart')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
