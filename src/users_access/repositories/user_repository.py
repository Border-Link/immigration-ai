from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import BaseUserManager
from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
from users_access.models.user import User


class UserRepository:

    @staticmethod
    def create_user(email, password):
        """
        Create a new user with profile.
        PII fields (first_name, last_name) are stored in UserProfile.
        """
        with transaction.atomic():
            normalized_email = BaseUserManager.normalize_email(email)
            user = User.objects.create(email=normalized_email, role="user")

            user.set_password(password)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.save(using=User.objects._db)
            
            user.full_clean()
            return user

    @staticmethod
    def create_superuser(email, password):
        user = UserRepository.create_user(email, password)
        user.role = "admin"
        user.is_superuser = True
        user.is_staff = True

        user.full_clean()
        user.save()
        return user

    @staticmethod
    def activate_user(user):
        with transaction.atomic():
            user.is_verified = True

            user.full_clean()
            user.save()
            return user

    @staticmethod
    def update_password(user, password):
        with transaction.atomic():
            user.password = make_password(password)

            user.full_clean()
            user.save()
            return user

    @staticmethod
    def is_verified(user):
        with transaction.atomic():
            user.is_verified = True
            user.full_clean()
            user.save()
            return user


    @staticmethod
    def update_last_assigned_at(user):
        """Update last assigned time for reviewer assignment tracking."""
        from django.utils import timezone
        with transaction.atomic():
            user.last_assigned_at = timezone.now()
            user.full_clean()
            user.save()
            return user

    @staticmethod
    def update_user(user, **fields):
        """Update user fields."""
        return BaseRepositoryMixin.update_model_fields(
            user,
            **fields,
            cache_keys=[f'user:{user.id}', f'user:email:{user.email}']
        )
