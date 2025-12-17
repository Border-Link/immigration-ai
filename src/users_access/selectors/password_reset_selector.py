from users_access.models import PasswordReset


class PasswordResetSelector:

    @staticmethod
    def get_by_user(user):
        return PasswordReset.objects.filter(user=user).first()
