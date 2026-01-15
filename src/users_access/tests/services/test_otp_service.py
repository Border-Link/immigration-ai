"""
Tests for OTPService.
All tests use services, not direct model access.
"""
import pytest
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestOTPService:
    """Tests for OTPService."""

    def test_create_otp(self, otp_service, test_user):
        """Test creating OTP."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        assert otp is not None
        assert otp.user == test_user

    def test_verify_otp(self, otp_service, test_user):
        """Test verifying OTP."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        user = otp_service.verify_otp("123456", "test_token")
        assert user == test_user
        # Verify OTP is marked as verified
        from users_access.selectors.otp_selector import OTPSelector
        otp_obj = OTPSelector.get_by_endpoint("test_token")
        assert otp_obj.is_verified is True

    def test_verify_otp_invalid(self, otp_service):
        """Test verifying invalid OTP."""
        result = otp_service.verify_otp("wrong", "wrong_token")
        assert result is False

    def test_get_by_endpoint(self, otp_service, test_user):
        """Test getting OTP by endpoint token."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        found = otp_service.get_by_endpoint("test_token")
        assert found == otp

    def test_get_last_unverified_otp(self, otp_service, test_user):
        """Test getting last unverified OTP."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        found = otp_service.get_last_unverified_otp(test_user)
        assert found == otp

    def test_cleanup_expired_otp(self, otp_service, test_user):
        """Test cleaning up expired OTPs."""
        # Create expired OTP via repository (needed for expiration)
        from users_access.repositories.otp_repository import OTPRepository
        expired_otp = OTPRepository.create_otp(
            user=test_user,
            otp="123456",
            endpoint_token="expired_token",
            otp_type="registration"
        )
        # Manually set expiration to past
        expired_otp.expires_at = timezone.now() - timedelta(minutes=1)
        expired_otp.save()
        
        result = otp_service.cleanup_expired_otp()
        assert result is not None
        # Verify expired OTP is cleaned up
        from users_access.selectors.otp_selector import OTPSelector
        found = OTPSelector.get_by_endpoint("expired_token")
        assert found is None

    def test_resend_otp(self, otp_service, test_user):
        """Test resending OTP."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        new_otp = "654321"
        resend_otp = otp_service.resend_otp(otp, new_otp)
        assert resend_otp.otp == new_otp
        assert resend_otp.is_verified is False

    def test_get_by_endpoint_and_user(self, otp_service, test_user):
        """Test getting OTP by endpoint and user."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        found = otp_service.get_by_endpoint_and_user("test_token", test_user)
        assert found == otp

    def test_verify_otp_expired(self, otp_service, test_user):
        """Test verifying expired OTP."""
        from users_access.repositories.otp_repository import OTPRepository
        expired_otp = OTPRepository.create_otp(
            user=test_user,
            otp="123456",
            endpoint_token="expired_token",
            otp_type="registration"
        )
        expired_otp.expires_at = timezone.now() - timedelta(minutes=1)
        expired_otp.save()
        
        result = otp_service.verify_otp("123456", "expired_token")
        assert result is False

    def test_verify_otp_already_verified(self, otp_service, test_user):
        """Test verifying already verified OTP."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        # Verify once
        user = otp_service.verify_otp("123456", "test_token")
        assert user == test_user
        # Try to verify again
        result = otp_service.verify_otp("123456", "test_token")
        assert result is False

    def test_verify_otp_wrong_otp(self, otp_service, test_user):
        """Test verifying with wrong OTP code."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        result = otp_service.verify_otp("654321", "test_token")
        assert result is False

    def test_verify_otp_wrong_token(self, otp_service, test_user):
        """Test verifying with wrong endpoint token."""
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        result = otp_service.verify_otp("123456", "wrong_token")
        assert result is False

    def test_get_by_endpoint_not_found(self, otp_service):
        """Test getting OTP by non-existent endpoint."""
        found = otp_service.get_by_endpoint("nonexistent")
        assert found is None

    def test_get_last_unverified_otp_none(self, otp_service, test_user):
        """Test getting last unverified OTP when none exists."""
        # Create verified OTP
        otp = otp_service.create(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        otp_service.verify_otp("123456", "test_token")
        found = otp_service.get_last_unverified_otp(test_user)
        assert found is None

    def test_resend_otp_updates_expiration(self, otp_service, test_user):
        """Test resending OTP updates expiration."""
        from users_access.repositories.otp_repository import OTPRepository
        otp = OTPRepository.create_otp(
            user=test_user,
            otp="123456",
            endpoint_token="test_token",
            otp_type="registration"
        )
        original_expires = otp.expires_at
        new_otp = "654321"
        resend_otp = otp_service.resend_otp(otp, new_otp)
        assert resend_otp.otp == new_otp
        assert resend_otp.expires_at > original_expires
