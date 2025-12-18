from typing import Dict
from django.db import transaction
from users_access.models.user_settings import UserSetting
from helpers.totp import TOTPAuthenticator


class UserSettingRepository:

    @staticmethod
    def create_user_setting(user):
        """Create user settings for a user."""
        with transaction.atomic():
            settings = UserSetting.objects.create(user=user)
            settings.full_clean()
            settings.save()
            return settings

    @staticmethod
    def update_settings(settings, settings_data: Dict):
        """Update settings fields."""
        with transaction.atomic():
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            settings.full_clean()
            settings.save()
            return settings

    @staticmethod
    def delete_settings(settings):
        """Delete user settings."""
        with transaction.atomic():
            settings.delete()
            return True

    @staticmethod
    def enable_2fa(settings):
        """Enable 2FA for user settings."""
        with transaction.atomic():
            secret = TOTPAuthenticator.generate_totp()
            settings.two_factor_auth = True
            settings.totp_secret = secret
            settings.full_clean()
            settings.save()
            return settings

    @staticmethod
    def disable_2fa(settings):
        """Disable 2FA for user settings."""
        with transaction.atomic():
            settings.two_factor_auth = False
            settings.totp_secret = None
            settings.full_clean()
            settings.save()
            return settings
