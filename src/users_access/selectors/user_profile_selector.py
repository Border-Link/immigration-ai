from users_access.models.user_profile import UserProfile


class UserProfileSelector:

    @staticmethod
    def get_by_user(user):
        """Get profile by user with related objects."""
        return UserProfile.objects.select_related(
            'user',
            'nationality',
            'state_province',
            'state_province__country'
        ).get(user=user)

    @staticmethod
    def get_by_user_id(user_id: str):
        """Get profile by user ID with related objects."""
        return UserProfile.objects.select_related(
            'user',
            'nationality',
            'state_province',
            'state_province__country'
        ).get(user_id=user_id)

    @staticmethod
    def profile_exists(user) -> bool:
        """Check if profile exists for user."""
        return UserProfile.objects.filter(user=user).exists()

    @staticmethod
    def get_by_nationality(country_code: str):
        """Get all profiles with specific nationality."""
        return UserProfile.objects.select_related(
            'user',
            'nationality',
            'state_province',
            'state_province__country'
        ).filter(
            nationality__code=country_code,
            nationality__is_active=True
        )

    @staticmethod
    def get_by_country(country):
        """Get all profiles for a country."""
        return UserProfile.objects.select_related(
            'user',
            'nationality',
            'state_province',
            'state_province__country'
        ).filter(nationality=country)

    @staticmethod
    def get_with_consent(consent_given: bool = True):
        """Get profiles with/without consent."""
        return UserProfile.objects.select_related(
            'user',
            'nationality',
            'state_province',
            'state_province__country'
        ).filter(consent_given=consent_given)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return UserProfile.objects.none()
