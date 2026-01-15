from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.user_profile_service import UserProfileService
from users_access.serializers.user_profile.profile_serializer import (
    UserProfileSerializer,
    UserProfileUpdateSerializer
)


class UserProfileAPI(AuthAPI):
    """Unified API for user profile - GET, PATCH, POST operations."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        """Get user profile."""
        profile = UserProfileService.get_profile(request.user)
        if not profile:
            return self.api_response(
                message="Profile not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Profile retrieved successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request):
        """Create user profile (if it doesn't exist)."""
        profile = UserProfileService.get_profile(request.user)
        if profile:
            return self.api_response(
                message="Profile already exists.",
                data=UserProfileSerializer(profile).data,
                status_code=status.HTTP_200_OK
            )

        # Profile will be created by get_profile if it doesn't exist
        profile = UserProfileService.get_profile(request.user)
        return self.api_response(
            message="Profile created successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_201_CREATED
        )

    def patch(self, request):
        """Update user profile - handles all profile fields."""
        serializer = UserProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user = request.user

        # Update basic profile fields (names, date_of_birth)
        basic_fields = {}
        if 'first_name' in validated_data:
            basic_fields['first_name'] = validated_data['first_name']
        if 'last_name' in validated_data:
            basic_fields['last_name'] = validated_data['last_name']
        if 'date_of_birth' in validated_data:
            basic_fields['date_of_birth'] = validated_data['date_of_birth']

        profile = None
        if basic_fields:
            profile = UserProfileService.update_profile(user, **basic_fields)

        # Update nationality if provided
        if 'country_code' in validated_data:
            country_code = validated_data.get('country_code')
            state_code = validated_data.get('state_code')
            if country_code:
                profile = UserProfileService.update_nationality(
                    user,
                    country_code=country_code,
                    state_code=state_code
                )

        # Update consent if provided
        if 'consent_given' in validated_data:
            consent_given = validated_data.get('consent_given')
            if consent_given is not None:
                profile = UserProfileService.update_consent(user, consent_given)

        # If no updates were made, get the current profile
        if not profile:
            profile = UserProfileService.get_profile(user)

        if not profile:
            return self.api_response(
                message="Error updating profile.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="Profile updated successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK
        )

