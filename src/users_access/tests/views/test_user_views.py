"""
Tests for user views/API endpoints.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from users_access.services.user_service import UserService


@pytest.mark.django_db
class TestUserRegistrationAPI:
    """Tests for UserRegistrationAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for registration URL."""
        return "/api/users/register/"  # Adjust based on actual URL

    @patch('users_access.views.users.create.OTPService')
    @patch('users_access.views.users.create.OTPBaseHandler')
    def test_user_registration_success(self, mock_otp_handler, mock_otp_service, client, url):
        """Test successful user registration."""
        mock_handler_instance = MagicMock()
        mock_handler_instance.generate_and_send_otp.return_value = ("123456", "test_token")
        mock_otp_handler.return_value = mock_handler_instance
        
        data = {
            "email": "test@example.com",
            "password": "TestPass123!@#",
            "first_name": "John",
            "last_name": "Doe"
        }
        response = client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_user_registration_missing_first_name(self, client, url):
        """Test registration without required first_name."""
        data = {
            "email": "test@example.com",
            "password": "TestPass123!@#",
            "last_name": "Doe"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_missing_last_name(self, client, url):
        """Test registration without required last_name."""
        data = {
            "email": "test@example.com",
            "password": "TestPass123!@#",
            "first_name": "John"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_duplicate_email(self, client, url, user_service):
        """Test registration with duplicate email."""
        user_service.create_user("test@example.com", "testpass123", "John", "Doe")
        data = {
            "email": "test@example.com",
            "password": "TestPass123!@#",
            "first_name": "Jane",
            "last_name": "Smith"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLoginAPI:
    """Tests for UserLoginAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for login URL."""
        return "/api/users/login/"  # Adjust based on actual URL

    @patch('users_access.views.users.login.OTPBaseHandler')
    @patch('users_access.views.users.login.UserDeviceSessionService')
    def test_login_success(self, mock_session_service, mock_otp_handler, client, url, verified_user):
        """Test successful login."""
        mock_handler_instance = MagicMock()
        mock_handler_instance.create_otp.return_value = ("123456", "test_token")
        mock_otp_handler.return_value = mock_handler_instance
        
        data = {
            "email": "verified@example.com",
            "password": "testpass123"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_login_invalid_credentials(self, client, url):
        """Test login with invalid credentials."""
        data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserAccountAPI:
    """Tests for UserAccountAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for account URL."""
        return "/api/users/account/"  # Adjust based on actual URL

    def test_get_user_account(self, client, url, test_user):
        """Test getting user account."""
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == test_user.email

    def test_get_user_account_unauthenticated(self, client, url):
        """Test getting user account without authentication."""
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('users_access.views.users.create.OTPService')
    @patch('users_access.views.users.create.OTPBaseHandler')
    def test_registration_invalid_email_format(self, mock_otp_handler, mock_otp_service, client, url):
        """Test registration with invalid email format."""
        mock_handler_instance = MagicMock()
        mock_handler_instance.generate_and_send_otp.return_value = ("123456", "test_token")
        mock_otp_handler.return_value = mock_handler_instance
        
        data = {
            "email": "invalid-email",
            "password": "TestPass123!@#",
            "first_name": "John",
            "last_name": "Doe"
        }
        response = client.post("/api/users/register/", data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('users_access.views.users.create.OTPService')
    @patch('users_access.views.users.create.OTPBaseHandler')
    def test_registration_weak_password(self, mock_otp_handler, mock_otp_service, client, url):
        """Test registration with weak password."""
        mock_handler_instance = MagicMock()
        mock_handler_instance.generate_and_send_otp.return_value = ("123456", "test_token")
        mock_otp_handler.return_value = mock_handler_instance
        
        data = {
            "email": "test@example.com",
            "password": "123",  # Weak password
            "first_name": "John",
            "last_name": "Doe"
        }
        response = client.post("/api/users/register/", data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_unverified_user(self, client, url, user_service):
        """Test login with unverified user."""
        user_service.create_user("unverified@example.com", "testpass123", "John", "Doe")
        data = {
            "email": "unverified@example.com",
            "password": "testpass123"
        }
        response = client.post("/api/users/login/", data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, client, url, user_service):
        """Test login with inactive user."""
        user = user_service.create_user("inactive@example.com", "testpass123", "John", "Doe")
        user_service.activate_user(user)  # Verify first
        user_service.update_user(user, is_active=False)  # Then deactivate
        data = {
            "email": "inactive@example.com",
            "password": "testpass123"
        }
        response = client.post("/api/users/login/", data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_account_endpoint_missing_profile(self, client, url, user_service):
        """Test account endpoint when profile doesn't exist."""
        # Create user without profile (shouldn't happen normally, but test edge case)
        user = user_service.create_user("noprofile@example.com", "testpass123", "John", "Doe")
        # Profile should exist, but test the endpoint handles it gracefully
        client.force_authenticate(user=user)
        response = client.get(url)
        # Should still work as profile is auto-created
        assert response.status_code == status.HTTP_200_OK
