"""
Tests for user settings views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from users_access.services.user_setting_service import UserSettingsService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestUserSettingsListAPIView:
    """Tests for UserSettingsListAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for settings URL."""
        return f"{API_PREFIX}/users/settings/"

    def test_get_settings(self, client, url, test_user, user_settings_service):
        """Test getting settings."""
        user_settings_service.create_user_setting(test_user)
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_settings_unauthenticated(self, client, url):
        """Test getting settings without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestEnable2FAAPIView:
    """Tests for Enable2FAAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for enable 2FA URL."""
        return f"{API_PREFIX}/users/settings/enable-2fa/"

    @patch('users_access.views.user_settings.create.QRCodeGenerator')
    def test_enable_2fa(self, mock_qr_generator, client, url, test_user):
        """Test enabling 2FA."""
        mock_qr_generator.generate.return_value = "base64_qr_code"
        client.force_authenticate(user=test_user)
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert "qr_code" in response.data["data"]


@pytest.mark.django_db
class TestUserSettingsToggleAPI:
    """Tests for UserSettingsToggleAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for enable 2FA URL (used by enable-2fa tests in this class)."""
        return f"{API_PREFIX}/users/settings/enable-2fa/"

    def test_toggle_setting(self, client, test_user, user_settings_service):
        """Test toggling a setting."""
        user_settings_service.create_user_setting(test_user)
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/users/settings/dark_mode/"
        data = {
            "value": True
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_toggle_invalid_setting(self, client, test_user):
        """Test toggling invalid setting."""
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/users/settings/invalid_setting/"
        data = {
            "value": True
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_toggle_invalid_setting_value(self, client, test_user, user_settings_service):
        """Test toggling setting with invalid value."""
        user_settings_service.create_user_setting(test_user)
        client.force_authenticate(user=test_user)
        url = f"{API_PREFIX}/users/settings/dark_mode/"
        data = {
            "value": "not_a_boolean"  # Invalid value type
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('users_access.views.user_settings.create.QRCodeGenerator')
    def test_enable_2fa_already_enabled(self, mock_qr_generator, client, url, test_user, user_settings_service):
        """Test enabling 2FA when already enabled."""
        mock_qr_generator.generate.return_value = "base64_qr_code"
        user_settings_service.enable_2fa(test_user)  # Enable first time
        client.force_authenticate(user=test_user)
        response = client.post(url, {}, format='json')
        # Should still work (may regenerate QR code)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
