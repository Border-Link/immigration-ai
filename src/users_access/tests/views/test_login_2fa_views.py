"""
Tests for login 2FA views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from users_access.services.otp_services import OTPService

API_PREFIX = "/api/v1/auth"

@pytest.mark.django_db
class TestTwoFactorVerificationAPIView:
    """Tests for TwoFactorVerificationAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for 2FA verification URL."""
        return f"{API_PREFIX}/users/login/verify/{endpoint_token}/"

    @patch('users_access.views.users.login_2fa.TOTPAuthenticator')
    @patch('users_access.views.users.login_2fa.UserDeviceSessionService')
    def test_2fa_verification_success(self, mock_session_service, mock_totp, client, verified_user, user_settings_service):
        """Test successful 2FA verification."""
        user_settings_service.enable_2fa(verified_user)
        otp = OTPService.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="login"
        )
        
        mock_totp.verify_totp.return_value = True
        
        url = f"{API_PREFIX}/users/login/verify/test_token/"
        data = {
            "otp": "123456",
            "is_2fa": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_2fa_verification_invalid_otp(self, client):
        """Test invalid OTP verification."""
        url = f"{API_PREFIX}/users/login/verify/invalid_token/"
        data = {
            "otp": "wrong",
            "is_2fa": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_2fa_verification_expired_otp(self, client, verified_user, otp_service):
        """Test verification with expired OTP."""
        from datetime import timedelta
        from django.utils import timezone
        from users_access.repositories.otp_repository import OTPRepository
        
        expired_otp = OTPRepository.create_otp(
            user=verified_user,
            otp="123456",
            endpoint_token="expired_token",
            otp_type="login"
        )
        expired_otp.expires_at = timezone.now() - timedelta(minutes=1)
        expired_otp.save()
        
        url = f"{API_PREFIX}/users/login/verify/expired_token/"
        data = {
            "otp": "123456",
            "is_2fa": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_2fa_verification_already_verified(self, client, verified_user, otp_service):
        """Test verification with already verified OTP."""
        otp = otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="login"
        )
        # Verify once
        otp_service.verify_otp("123456", "test_token")
        
        url = f"{API_PREFIX}/users/login/verify/test_token/"
        data = {
            "otp": "123456",
            "is_2fa": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_2fa_verification_missing_otp(self, client):
        """Test verification with missing OTP."""
        url = f"{API_PREFIX}/users/login/verify/test_token/"
        data = {
            "is_2fa": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_2fa_verification_empty_otp(self, client):
        """Test verification with empty OTP."""
        url = f"{API_PREFIX}/users/login/verify/test_token/"
        data = {
            "otp": "",
            "is_2fa": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_2fa_verification_requires_password_change(self, client, verified_user, otp_service, user_service):
        """Users flagged for password change cannot complete login."""
        user_service.update_user(verified_user, must_change_password=True)
        otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="change_pw_token",
            otp_type="login"
        )
        url = f"{API_PREFIX}/users/login/verify/change_pw_token/"
        data = {
            "otp": "123456",
            "is_2fa": False
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data.get("password_change_required") is True

    @patch('users_access.views.users.login_2fa.TOTPAuthenticator')
    def test_2fa_verification_totp_failure(self, mock_totp, client, verified_user, user_settings_service, otp_service):
        """Test 2FA verification with TOTP failure."""
        user_settings_service.enable_2fa(verified_user)
        otp = otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="login"
        )
        
        mock_totp.verify_totp.return_value = False
        
        url = f"{API_PREFIX}/users/login/verify/test_token/"
        data = {
            "otp": "123456",
            "is_2fa": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
