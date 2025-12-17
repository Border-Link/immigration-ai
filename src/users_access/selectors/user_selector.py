import logging
from users_access.models import User

logger = logging.getLogger('django')


class UserSelector:

    @staticmethod
    def get_all():
        return User.objects.all()

    @staticmethod
    def get_by_email(email: str):
        return User.objects.filter(email__iexact=email).first()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(email__iexact=email).exists()
