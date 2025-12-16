import logging
from helpers.cache_utils import cache_result
from users_access.models.user_settings import UserSetting

logger = logging.getLogger('django')


class UserSettingsService:
    def __init__(self):
        self.manager = UserSetting.objects

    @cache_result(timeout=3600, keys=['user_id'])
    def get_settings(self, user_id: str):
        return self.manager.get_settings(user_id)

    def create_default_settings(self, user_id: str):
        return self.manager.create_user_setting(user_id)

    def update_settings(self, user_id: str, settings_data: dict):
        return self.manager.update_settings(user_id, settings_data)

    def delete_settings(self, user_id: str):
        return self.manager.delete_settings(user_id)

    def enable_2fa(self, user_id: str):
        return self.manager.enable_2fa(user_id)