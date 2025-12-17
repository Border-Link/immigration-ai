from users_access.models.user_settings import UserSetting
from users_access.repositories.user_setting_repository import UserSettingRepository
from users_access.selectors.user_setting_selector import UserSettingSelector
import logging

logger = logging.getLogger('django')


class UserSettingsService:

    @staticmethod
    def create_user_setting(user_id: str):
        try:
            return UserSettingRepository.create_user_setting(user_id)
        except Exception as e:
            logger.error(f"Error creating default settings for user {user_id}: {e}")
            return None

    @staticmethod
    def update_settings(user_id: str, settings_data: dict):
        try:
            return UserSettingRepository.update_settings(user_id, settings_data)
        except Exception as e:
            logger.error(f"Error updating settings for user {user_id}: {e}")
            return None

    @staticmethod
    def get_settings(user_id: str):
        try:
            settings = UserSettingSelector.get_settings(user_id)
            if not settings:
                logger.warning(f"Settings not found for user {user_id}")
            return settings
        except Exception as e:
            logger.error(f"Error fetching settings for user {user_id}: {e}")
            return None

    @staticmethod
    def delete_settings(user_id: str):
        try:
            return UserSettingRepository.delete_settings(user_id)
        except UserSetting.DoesNotExist:
            logger.warning(f"Settings not found for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting settings for user {user_id}: {e}")
            return False

    @staticmethod
    def enable_2fa(user_id: str):
        try:
            settings = UserSettingSelector.get_settings(user_id)
            if not settings:
                logger.warning(f"Settings not found for user {user_id}")
                return None
            # Skip if already enabled
            if settings.two_factor_auth and settings.totp_secret:
                logger.warning(f"2FA already enabled for user {user_id}")
                return settings

            return UserSettingRepository.enable_2fa(user_id)
        except Exception as e:
            logger.error(f"Error enabling 2FA for user {user_id}: {e}")
            return None
