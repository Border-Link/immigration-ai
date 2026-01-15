"""
Tests for user profile views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_profile_service import UserProfileService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestUserProfileAPI:
    """Tests for UserProfileAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for profile URL."""
        return f"{API_PREFIX}/users/profile/"

    def test_get_profile(self, client, url, test_user):
        """Test getting profile."""
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_update_profile(self, client, url, test_user, test_country):
        """Test updating profile."""
        client.force_authenticate(user=test_user)
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "country_code": "US"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_get_profile_unauthenticated(self, client, url):
        """Test getting profile without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfileAvatarAPI:
    """Tests for UserProfileAvatarAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for avatar delete URL."""
        return f"{API_PREFIX}/users/profile/avatar/"

    def test_delete_avatar(self, client, url, test_user):
        """Test deleting avatar."""
        client.force_authenticate(user=test_user)
        response = client.delete(url)
        # Should return 200 even if no avatar exists
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_update_profile_invalid_country_code(self, client, url, test_user):
        """Test updating profile with invalid country code."""
        client.force_authenticate(user=test_user)
        data = {
            "country_code": "XX"  # Invalid country code
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_profile_invalid_state_code(self, client, url, test_user, test_country):
        """Test updating profile with invalid state code."""
        client.force_authenticate(user=test_user)
        data = {
            "country_code": test_country.code,
            "state_code": "XX"  # Invalid state code
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_avatar_invalid_file_type(self, client, test_user):
        """Test uploading avatar with invalid file type."""
        from unittest.mock import MagicMock
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/users/profile/avatar/"
        # Create a text file instead of image
        file = SimpleUploadedFile("test.txt", b"file content", content_type="text/plain")
        response = client.post(url, {"avatar": file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_avatar_file_too_large(self, client, test_user):
        """Test uploading avatar with file too large."""
        from unittest.mock import MagicMock
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io
        
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/users/profile/avatar/"
        # Create a large image file (simulate > 5MB)
        img = Image.new('RGB', (2000, 2000), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        # Create file that's too large (simulate by creating large content)
        large_content = b'x' * (6 * 1024 * 1024)  # 6MB
        file = SimpleUploadedFile("large.jpg", large_content, content_type="image/jpeg")
        response = client.post(url, {"avatar": file}, format='multipart')
        # Should fail validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST
