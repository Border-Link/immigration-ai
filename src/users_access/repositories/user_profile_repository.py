from typing import Optional
from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
from users_access.models.user_profile import UserProfile
from users_access.models.state_province import StateProvince


class UserProfileRepository:

    @staticmethod
    def create_profile(user, first_name=None, last_name=None, nationality=None, 
                      state_province=None, date_of_birth=None, consent_given=False):
        """Create a new user profile."""
        with transaction.atomic():
            profile = UserProfile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                nationality=nationality,
                state_province=state_province,
                date_of_birth=date_of_birth,
                consent_given=consent_given
            )
            profile.full_clean()
            profile.save()
            return profile

    @staticmethod
    def update_profile(profile, **fields):
        """Update profile fields."""
        return BaseRepositoryMixin.update_model_fields(
            profile,
            **fields,
            cache_keys=[f'user_profile:{profile.id}', f'user_profile:user:{profile.user.id}']
        )

    @staticmethod
    def update_names(profile, first_name: Optional[str], last_name: Optional[str]):
        """Update user names."""
        with transaction.atomic():
            if first_name is not None:
                profile.first_name = first_name
            if last_name is not None:
                profile.last_name = last_name
            profile.full_clean()
            profile.save()
            return profile

    @staticmethod
    def update_nationality(profile, country, state_province: Optional[StateProvince] = None):
        """Update nationality and optionally state/province."""
        with transaction.atomic():
            profile.nationality = country
            profile.state_province = state_province
            profile.full_clean()
            profile.save()
            return profile

    @staticmethod
    def update_consent(profile, consent_given: bool):
        """Update GDPR consent."""
        with transaction.atomic():
            from django.utils import timezone
            profile.consent_given = consent_given
            if consent_given:
                profile.consent_timestamp = timezone.now()
            else:
                profile.consent_timestamp = None
            profile.full_clean()
            profile.save()
            return profile

    @staticmethod
    def update_avatar(profile, avatar):
        """Update profile avatar."""
        with transaction.atomic():
            old_avatar = profile.avatar
            profile.avatar = avatar
            profile.full_clean()
            profile.save()
            if old_avatar and old_avatar.name and old_avatar.name != profile.avatar.name:
                old_avatar.delete(save=False)
            return profile

    @staticmethod
    def remove_avatar(profile):
        """Remove profile avatar."""
        with transaction.atomic():
            old_avatar = profile.avatar
            profile.avatar = None
            profile.full_clean()
            profile.save()
            if old_avatar and old_avatar.name:
                old_avatar.delete(save=False)
            return profile

