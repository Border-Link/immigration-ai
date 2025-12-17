from users_access.models.user_settings import UserSetting

class UserSettingSelector:

    @staticmethod
    def get_settings(user_id: str):
        return UserSetting.objects.filter(user__id=user_id).first()
