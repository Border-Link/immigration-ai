from typing import Optional
from django.contrib.auth import authenticate
from main_system.utils.cache_utils import cache_result, invalidate_cache
from users_access.repositories.user_repository import UserRepository
from users_access.repositories.user_profile_repository import UserProfileRepository
from users_access.selectors.user_selector import UserSelector
from users_access.models.user import User as CustomUser
import logging

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    """
    Single namespace for all User-related cached reads.
    Any write operation must bump this namespace to avoid stale reads.
    """
    return "users"


class UserService:

    @staticmethod
    @invalidate_cache(namespace)
    def create_user(email, password, first_name=None, last_name=None):
        """
        Create a new user with profile.
        first_name and last_name are saved to UserProfile (not User table).
        Profile is auto-created by signal (post_save), then updated with names.
        """
        try:
            user = UserRepository.create_user(email, password)
            if user:
                # Profile is auto-created by signal (post_save), but we need to update it with names
                # Use UserProfileService to ensure profile exists and update names
                from users_access.services.user_profile_service import UserProfileService
                UserProfileService.update_names(user, first_name, last_name)
            return user
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace)
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
    @invalidate_cache(namespace)
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
    @cache_result(timeout=60, keys=["role"], namespace=namespace, user_scope="global")
    def get_by_role(role: str):
        """Get users by role (service wrapper around selector)."""
        try:
            return UserSelector.get_by_role(role)
        except Exception as e:
            logger.error(f"Error fetching users by role {role}: {e}")
            return UserSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace)  # 5 minutes - user list changes frequently
    def get_all():
        try:
            return UserSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []

    @staticmethod
    @cache_result(timeout=300, keys=['email'], namespace=namespace)  # 5 minutes - cache email existence checks
    def email_exists(email):
        try:
            return UserSelector.email_exists(email)
        except Exception as e:
            logger.error(f"Error checking if email exists: {e}")
            return False

    @staticmethod
    def login(email: str, password: str, request=None):
        # Don't cache login - security sensitive
        try:
            user: Optional[CustomUser] = authenticate(request, email=email, password=password)
            if not user:
                return None, "Invalid credentials entered."
            if not user.is_active:
                return None, "User is not active"
            if not user.is_verified:
                return None, "Email is not verified"
            return user, None
        except Exception as e:
            logger.exception(f"Error during login for {email}: {e}")
            return None, "Invalid credentials entered."

    @staticmethod
    @cache_result(timeout=600, keys=['email'], namespace=namespace)  # 10 minutes - cache user lookups by email
    def get_by_email(email):
        try:
            return UserSelector.get_by_email(email)
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=600, keys=['user_id'], namespace=namespace)  # 10 minutes - cache user lookups by ID
    def get_by_id(user_id):
        """Get user by ID."""
        try:
            return UserSelector.get_by_id(user_id)
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace)
    def update_user_last_assigned_at(user):
        """Update last assigned time for reviewer assignment tracking."""
        try:
            return UserRepository.update_last_assigned_at(user)
        except Exception as e:
            logger.error(f"Error updating last_assigned_at for user {user.email}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace)
    def delete_user(user_id: str) -> bool:
        """Delete a user (soft delete by deactivating)."""
        try:
            user = UserSelector.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            # Soft delete by deactivating
            UserRepository.update_user(user, is_active=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(role: str = None, is_active: bool = None, is_verified: bool = None, 
                       email: str = None, date_from=None, date_to=None):
        """Get users with filters."""
        try:
            users = UserSelector.get_all()
            
            # Apply filters
            if role:
                users = users.filter(role=role)
            if is_active is not None:
                users = users.filter(is_active=is_active)
            if is_verified is not None:
                users = users.filter(is_verified=is_verified)
            if email:
                users = users.filter(email__icontains=email)
            if date_from:
                users = users.filter(created_at__gte=date_from)
            if date_to:
                users = users.filter(created_at__lte=date_to)
            
            return users
        except Exception as e:
            logger.error(f"Error fetching filtered users: {e}")
            return UserSelector.get_none()

    @staticmethod
    @invalidate_cache(namespace)
    def activate_user_by_id(user_id: str):
        """Activate a user by ID."""
        try:
            user = UserSelector.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            return UserRepository.activate_user(user)
        except Exception as e:
            logger.error(f"Error activating user {user_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace)
    def deactivate_user_by_id(user_id: str):
        """Deactivate a user by ID."""
        try:
            user = UserSelector.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            return UserRepository.update_user(user, is_active=False)
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get user statistics."""
        try:
            from users_access.models.user import User
            from django.db.models import Count, Q
            
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            inactive_users = User.objects.filter(is_active=False).count()
            verified_users = User.objects.filter(is_verified=True).count()
            unverified_users = User.objects.filter(is_verified=False).count()
            
            users_by_role = dict(
                User.objects.values('role')
                .annotate(count=Count('id'))
                .order_by('role')
                .values_list('role', 'count')
            )
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'verified_users': verified_users,
                'unverified_users': unverified_users,
                'users_by_role': users_by_role,
            }
        except Exception as e:
            logger.error(f"Error fetching user statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'verified_users': 0,
                'unverified_users': 0,
                'users_by_role': {},
            }

    @staticmethod
    def get_user_activity(user_id: str):
        """Get user activity information."""
        try:
            user = UserSelector.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            
            return {
                'user_id': str(user.id),
                'email': user.email,
                'login_count': user.login_count,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                'last_assigned_at': user.last_assigned_at.isoformat() if user.last_assigned_at else None,
            }
        except Exception as e:
            logger.error(f"Error fetching user activity for {user_id}: {e}")
            return None
