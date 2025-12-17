from users_access.repositories.password_reset_repository import PasswordResetRepository
import logging

logger = logging.getLogger('django')


class PasswordResetService:

    @staticmethod
    def create_password_reset(user):
        try:
            return PasswordResetRepository.create_password_reset(user)
        except KeyError as e:
            logger.error(f"Missing required field: {e} for user {user.email}")
            return None
        except Exception as e:
            logger.error(f"Error while creating password reset for user {user.email}: {e}")
            return None
