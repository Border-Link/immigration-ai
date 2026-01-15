"""
Tests for forgot password views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from users_access.services.user_service import UserService
from users_access.services.otp_services import OTPService


@pytest.mark.django_db
class TestSendForgotPasswordOTPAPIView:
    """Tests for SendForgotPasswordOTPAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for forgot password URL."""
        return "/api/users/forgot-password/"  # Adjust based on actual URL

    @patch('users_access.views.users.forgot_password.OTPBaseHandler')
    def test_send_forgot_password_otp_success(self, mock_otp_handler, client, url, verified_user):
        """Test successful forgot password OTP send."""
        mock_handler_instance = MagicMock()
        mock_handler_instance.generate_and_send_otp.return_value = ("123456", "test_token")
        mock_otp_handler.return_value = mock_handler_instance
        
        data = {
            "email": "verified@example.com"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_send_forgot_password_otp_invalid_email(self, client, url):
        """Test forgot password with invalid email."""
        data = {
            "email": "nonexistent@example.com"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordResetOTPVerificationAPIView:
    """Tests for PasswordResetOTPVerificationAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for OTP verification URL."""
        return "/api/users/forgot-password/verify/{endpoint_token}/"  # Adjust based on actual URL

    def test_verify_otp_success(self, client, otp_service, verified_user):
        """Test successful OTP verification."""
        otp = otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="password_reset"
        )
        url = f"/api/users/forgot-password/verify/test_token/"
        data = {
            "otp": "123456"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_verify_otp_invalid(self, client):
        """Test invalid OTP verification."""
        url = "/api/users/forgot-password/verify/invalid_token/"
        data = {
            "otp": "wrong"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCreateNewPasswordTokenAPIView:
    """Tests for CreateNewPasswordTokenAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for create new password URL."""
        return "/api/users/forgot-password/reset/{endpoint_token}/"  # Adjust based on actual URL

    def test_create_new_password_success(self, client, otp_service, verified_user):
        """Test successful password reset."""
        otp = otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="password_reset"
        )
        # Verify OTP first
        otp_service.verify_otp("123456", "test_token")
        
        url = f"/api/users/forgot-password/reset/test_token/"
        data = {
            "new_password": "NewPass123!@#",
            "retype_password": "NewPass123!@#",
            "email": "verified@example.com"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_verify_otp_invalid_token(self, client):
        """Test OTP verification with invalid endpoint token."""
        url = "/api/users/forgot-password/verify/invalid_token_123/"
        data = {
            "otp": "123456"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_otp_expired(self, client, otp_service, verified_user):
        """Test OTP verification with expired OTP."""
        from datetime import timedelta
        from django.utils import timezone
        from users_access.repositories.otp_repository import OTPRepository
        
        expired_otp = OTPRepository.create_otp(
            user=verified_user,
            otp="123456",
            endpoint_token="expired_token",
            otp_type="password_reset"
        )
        expired_otp.expires_at = timezone.now() - timedelta(minutes=1)
        expired_otp.save()
        
        url = "/api/users/forgot-password/verify/expired_token/"
        data = {
            "otp": "123456"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_new_password_weak_password(self, client, otp_service, verified_user):
        """Test password reset with weak password."""
        otp = otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="password_reset"
        )
        otp_service.verify_otp("123456", "test_token")
        
        url = f"/api/users/forgot-password/reset/test_token/"
        data = {
            "new_password": "123",  # Weak password
            "retype_password": "123",
            "email": "verified@example.com"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_new_password_mismatch(self, client, otp_service, verified_user):
        """Test password reset with mismatched passwords."""
        otp = otp_service.create(
            user=verified_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="password_reset"
        )
        otp_service.verify_otp("123456", "test_token")
        
        url = f"/api/users/forgot-password/reset/test_token/"
        data = {
            "new_password": "NewPass123!@#",
            "retype_password": "DifferentPass123!@#",
            "email": "verified@example.com"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
