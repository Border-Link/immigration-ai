from users_access.repositories.password_reset_repository import PasswordResetRepository
from users_access.models.user import User
import logging

logger = logging.getLogger('django')


class PasswordResetService:

    @staticmethod
    def create_password_reset(user):
        try:
            # Guardrail: don't create password reset records for unsaved/invalid users
            user_id = getattr(user, "id", None)
            if not user_id or not User.objects.filter(id=user_id).exists():
                logger.warning("Password reset requested for non-existent user")
                return None
            return PasswordResetRepository.create_password_reset(user)
        except KeyError as e:
            logger.error(f"Missing required field: {e} for user {user.email}")
            return None
        except Exception as e:
            logger.error(f"Error while creating password reset for user {user.email}: {e}")
            return None
