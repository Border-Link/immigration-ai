"""
Tests for UserSettingsService.
All tests use services, not direct model access.
"""
import pytest
from users_access.services.user_setting_service import UserSettingsService


@pytest.mark.django_db
class TestUserSettingsService:
    """Tests for UserSettingsService."""

    def test_create_user_setting(self, user_settings_service, test_user):
        """Test creating user settings."""
        settings = user_settings_service.create_user_setting(test_user)
        assert settings is not None
        assert settings.user == test_user

    def test_update_settings(self, user_settings_service, test_user):
        """Test updating settings."""
        user_settings_service.create_user_setting(test_user)
        updated = user_settings_service.update_settings(
            test_user,
            {"dark_mode": True, "language": "fr"}
        )
        assert updated.dark_mode is True
        assert updated.language == "fr"

    def test_get_settings(self, user_settings_service, test_user):
        """Test getting settings."""
        settings = user_settings_service.create_user_setting(test_user)
        found = user_settings_service.get_settings(test_user)
        assert found == settings

    def test_enable_2fa(self, user_settings_service, test_user):
        """Test enabling 2FA."""
        settings = user_settings_service.enable_2fa(test_user)
        assert settings is not None
        assert settings.two_factor_auth is True
        assert settings.totp_secret is not None

    def test_disable_2fa(self, user_settings_service, test_user):
        """Test disabling 2FA."""
        user_settings_service.enable_2fa(test_user)
        settings = user_settings_service.disable_2fa(test_user)
        assert settings is not None
        assert settings.two_factor_auth is False
        assert settings.totp_secret is None

    def test_update_notification_preferences(self, user_settings_service, test_user):
        """Test updating notification preferences."""
        user_settings_service.create_user_setting(test_user)
        updated = user_settings_service.update_settings(
            test_user,
            {
                "email_notifications": False,
                "sms_notifications": False,
                "notify_case_status_updates": False
            }
        )
        assert updated.email_notifications is False
        assert updated.sms_notifications is False
        assert updated.notify_case_status_updates is False

    def test_delete_settings(self, user_settings_service, test_user):
        """Test deleting settings."""
        user_settings_service.create_user_setting(test_user)
        result = user_settings_service.delete_settings(test_user)
        assert result is True
        found = user_settings_service.get_settings(test_user)
        assert found is None

    def test_update_settings_empty_dict(self, user_settings_service, test_user):
        """Test updating settings with empty dict."""
        user_settings_service.create_user_setting(test_user)
        updated = user_settings_service.update_settings(test_user, {})
        assert updated is not None

    def test_get_settings_not_exists(self, user_settings_service, test_user):
        """Test getting settings when they don't exist."""
        # Settings should be auto-created
        found = user_settings_service.get_settings(test_user)
        assert found is not None

    def test_enable_2fa_twice(self, user_settings_service, test_user):
        """Test enabling 2FA twice."""
        settings1 = user_settings_service.enable_2fa(test_user)
        settings2 = user_settings_service.enable_2fa(test_user)
        assert settings2.two_factor_auth is True
        assert settings2.totp_secret is not None

    def test_disable_2fa_when_not_enabled(self, user_settings_service, test_user):
        """Test disabling 2FA when not enabled."""
        user_settings_service.create_user_setting(test_user)
        settings = user_settings_service.disable_2fa(test_user)
        assert settings.two_factor_auth is False
        assert settings.totp_secret is None
