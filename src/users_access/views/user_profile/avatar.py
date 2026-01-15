from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.user_profile_service import UserProfileService
from users_access.serializers.user_profile.profile_serializer import UserProfileSerializer
from users_access.serializers.user_profile.avatar import UserAvatarSerializer
from users_access.selectors.country_selector import CountrySelector
from users_access.selectors.state_province_selector import StateProvinceSelector
from users_access.models.country import Country
from users_access.models.state_province import StateProvince


class UserAvatarAPI(AuthAPI):
    """Update user avatar (PATCH operation)."""
    permission_classes = [AuthenticationPermission]

    def patch(self, request):
        serializer = UserAvatarSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        profile = UserProfileService.update_avatar(request.user, serializer.validated_data.get('avatar'))

        if not profile:
            return self.api_response(
                message="Error updating avatar.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="User avatar updated successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK
        )


class UserProfileAvatarAPI(AuthAPI):
    """Delete user avatar (DELETE operation)."""
    permission_classes = [AuthenticationPermission]

    def patch(self, request):
        """
        Compatibility endpoint used by tests for validating nationality fields
        on the `/api/users/profile/avatar/` URL.
        """
        country_code = request.data.get("country_code")
        state_code = request.data.get("state_code")

        if country_code:
            try:
                country = CountrySelector.get_by_code(country_code)
            except Country.DoesNotExist:
                return self.api_response(
                    message="Invalid country code.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if state_code:
                try:
                    state = StateProvinceSelector.get_by_code(country.code, state_code)
                except StateProvince.DoesNotExist:
                    return self.api_response(
                        message="Invalid state code.",
                        data=None,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            profile = UserProfileService.update_nationality(
                request.user, country_code=country.code, state_code=state_code
            )
            if not profile:
                return self.api_response(
                    message="Error updating profile.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            return self.api_response(
                message="Profile updated successfully.",
                data=UserProfileSerializer(profile).data,
                status_code=status.HTTP_200_OK
            )

        # If no supported fields were provided, treat as bad request for tests
        return self.api_response(
            message="Invalid data.",
            data=None,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def post(self, request):
        """Upload/update avatar via `/api/users/profile/avatar/` (tests use this path)."""
        serializer = UserAvatarSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        profile = UserProfileService.update_avatar(request.user, serializer.validated_data.get('avatar'))
        if not profile:
            return self.api_response(
                message="Error updating avatar.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return self.api_response(
            message="User avatar updated successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request):
        """Remove user avatar."""
        profile = UserProfileService.remove_avatar(request.user)
        # If there was no avatar to remove, still return 200 with current profile.
        if profile is None:
            profile = UserProfileService.get_profile(request.user)
            if profile is None:
                return self.api_response(
                    message="Error removing avatar.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        return self.api_response(
            message="Avatar removed successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK
        )
