from users_access.models.user_settings import UserSetting
from users_access.repositories.user_setting_repository import UserSettingRepository
from users_access.selectors.user_setting_selector import UserSettingSelector
from users_access.selectors.user_selector import UserSelector
import logging

logger = logging.getLogger('django')


class UserSettingsService:

    @staticmethod
    def create_user_setting(user):
        """Create user settings for a user."""
        try:
            return UserSettingRepository.create_user_setting(user)
        except Exception as e:
            logger.error(f"Error creating default settings for user {user.id}: {e}")
            return None

    @staticmethod
    def update_settings(user, settings_data: dict):
        """Update user settings."""
        try:
            settings = UserSettingSelector.get_settings_by_user(user)
            if not settings:
                settings = UserSettingRepository.create_user_setting(user)
            return UserSettingRepository.update_settings(settings, settings_data)
        except Exception as e:
            logger.error(f"Error updating settings for user {user.id}: {e}")
            return None

    @staticmethod
    def get_settings(user):
        """Get user settings."""
        try:
            settings = UserSettingSelector.get_settings_by_user(user)
            return settings
        except Exception as e:
            logger.error(f"Error fetching settings for user {user.id}: {e}")
            return None

    @staticmethod
    def delete_settings(user):
        """Delete user settings."""
        try:
            settings = UserSettingSelector.get_settings_by_user(user)
            if not settings:
                logger.warning(f"Settings not found for user {user.id}")
                return False
            return UserSettingRepository.delete_settings(settings)
        except UserSetting.DoesNotExist:
            logger.warning(f"Settings not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting settings for user {user.id}: {e}")
            return False

    @staticmethod
    def enable_2fa(user):
        """Enable 2FA for user."""
        try:
            settings = UserSettingSelector.get_settings_by_user(user)
            if not settings:
                settings = UserSettingRepository.create_user_setting(user)
            # Skip if already enabled
            if settings.two_factor_auth and settings.totp_secret:
                logger.warning(f"2FA already enabled for user {user.id}")
                return settings
            return UserSettingRepository.enable_2fa(settings)
        except Exception as e:
            logger.error(f"Error enabling 2FA for user {user.id}: {e}")
            return None

    @staticmethod
    def disable_2fa(user):
        """Disable 2FA for user."""
        try:
            settings = UserSettingSelector.get_settings_by_user(user)
            if not settings:
                logger.warning(f"Settings not found for user {user.id}")
                return None
            return UserSettingRepository.disable_2fa(settings)
        except Exception as e:
            logger.error(f"Error disabling 2FA for user {user.id}: {e}")
            return None
