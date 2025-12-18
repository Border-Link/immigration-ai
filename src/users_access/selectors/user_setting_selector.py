from users_access.models.user_settings import UserSetting


class UserSettingSelector:

    @staticmethod
    def get_settings(user_id: str):
        """Get user settings with user."""
        return UserSetting.objects.filter(user__id=user_id).first()

    @staticmethod
    def get_settings_by_user(user):
        """Get user settings by user object."""
        return UserSetting.objects.filter(user=user).first()

