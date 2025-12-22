from typing import Optional
from django.contrib.auth import authenticate
from helpers import fields as input_fields
from users_access.repositories.user_repository import UserRepository
from users_access.repositories.user_profile_repository import UserProfileRepository
from users_access.selectors.user_selector import UserSelector
from users_access.models.user import User as CustomUser
import logging

logger = logging.getLogger('django')


class UserService:

    @staticmethod
    def create_user(email, password, first_name=None, last_name=None):
        try:
            user = UserRepository.create_user(email, password)
            if user and (first_name or last_name):
                # Profile is auto-created by signal, but we update it with names
                from users_access.selectors.user_profile_selector import UserProfileSelector
                try:
                    profile = UserProfileSelector.get_by_user(user)
                    UserProfileRepository.update_names(profile, first_name, last_name)
                except Exception:
                    # If profile doesn't exist yet, create it
                    UserProfileRepository.create_profile(user, first_name, last_name)
            return user
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return None

    @staticmethod
    def create_superuser(email, password, first_name=None, last_name=None):
        try:
            user = UserRepository.create_superuser(email, password)
            if user and (first_name or last_name):
                from users_access.selectors.user_profile_selector import UserProfileSelector
                try:
                    profile = UserProfileSelector.get_by_user(user)
                    UserProfileRepository.update_names(profile, first_name, last_name)
                except Exception:
                    UserProfileRepository.create_profile(user, first_name, last_name)
            return user
        except Exception as e:
            logger.error(f"Error creating superuser {email}: {e}")
            return None

    @staticmethod
    def update_user(user, **fields):
        try:
            return UserRepository.update_user(user, **fields)
        except Exception as e:
            logger.error(f"Error updating user {user.email}: {e}")
            return None

    @staticmethod
    def update_avatar(user, avatar):
        """Update user avatar - delegates to UserProfileService."""
        try:
            from users_access.services.user_profile_service import UserProfileService
            return UserProfileService.update_avatar(user, avatar)
        except Exception as e:
            logger.error(f"Error updating avatar for user {user.email}: {e}")
            return None

    @staticmethod
    def remove_avatar(user):
        """Remove user avatar - delegates to UserProfileService."""
        try:
            from users_access.services.user_profile_service import UserProfileService
            return UserProfileService.remove_avatar(user)
        except Exception as e:
            logger.error(f"Error removing avatar for user {user.email}: {e}")
            return None

    @staticmethod
    def update_names(user, first_name=None, last_name=None):
        """Update user names - delegates to UserProfileService."""
        try:
            from users_access.services.user_profile_service import UserProfileService
            return UserProfileService.update_names(user, first_name, last_name)
        except Exception as e:
            logger.error(f"Error updating names for user {user.email}: {e}")
            return None

    @staticmethod
    def activate_user(user):
        try:
            return UserRepository.activate_user(user)
        except Exception as e:
            logger.error(f"Error activating user {user.email}: {e}")
            return None

    @staticmethod
    def update_password(user, password):
        try:
            return UserRepository.update_password(user, password)
        except Exception as e:
            logger.error(f"Error updating password for user {user.email}: {e}")
            return None

    @staticmethod
    def is_verified(user):
        try:
            return UserRepository.is_verified(user)
        except Exception as e:
            logger.error(f"Error verifying user {user.email}: {e}")
            return None

    @staticmethod
    def get_all():
        try:
            return UserSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []

    @staticmethod
    def email_exists(email):
        try:
            return UserSelector.email_exists(email)
        except Exception as e:
            logger.error(f"Error checking if email exists: {e}")
            return False

    @staticmethod
    def login(email: str, password: str, request=None):
        try:
            user: Optional[CustomUser] = authenticate(request, email=email, password=password)
            if not user:
                return None, input_fields.INVALID_CREDENTIALS
            if not user.is_active:
                return None, input_fields.USER_NOT_ACTIVE
            if not user.is_verified:
                return None, input_fields.EMAIL_NOT_VERIFIED
            return user, None
        except Exception as e:
            logger.exception(f"Error during login for {email}: {e}")
            return None, input_fields.INVALID_CREDENTIALS

    @staticmethod
    def get_by_email(email):
        try:
            return UserSelector.get_by_email(email)
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        try:
            return UserSelector.get_by_id(user_id)
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {e}")
            return None

