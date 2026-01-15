"""
Tests for resend 2FA views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from users_access.services.otp_services import OTPService


API_PREFIX = "/api/v1/auth"


@pytest.mark.django_db
class TestResendTwoFactorTokenAPIView:
    """Tests for ResendTwoFactorTokenAPIView."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for resend 2FA URL."""
        return f"{API_PREFIX}/users/login/resend-2fa/{endpoint_token}/"

    @patch('users_access.views.users.resend_2fa.send_otp_email_task')
    def test_resend_2fa_success(self, mock_email_task, client, otp_service, test_user):
        """Test successful 2FA resend."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="login"
        )
        url = f"{API_PREFIX}/users/login/resend-2fa/test_token/"
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_resend_2fa_invalid_token(self, client):
        """Test resend 2FA with invalid token."""
        url = f"{API_PREFIX}/users/login/resend-2fa/invalid_token/"
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
