from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.user_profile_service import UserProfileService
from users_access.serializers.user_profile.profile_serializer import UserProfileSerializer
from users_access.serializers.users.add_avatar import UserAvatarSerializer


class UserAvatarAPI(AuthAPI):
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
