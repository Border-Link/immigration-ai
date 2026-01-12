from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.user_profile_service import UserProfileService
from users_access.serializers.user_profile.profile_serializer import UserProfileSerializer
from users_access.serializers.users.names_update import NamesUpdateSerializer


class UserNamesUpdateAPI(AuthAPI):
    permission_classes = [AuthenticationPermission]
    serializer_class = NamesUpdateSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')
        profile = UserProfileService.update_names(request.user, first_name, last_name)

        if not profile:
            return self.api_response(
                message="Error updating names.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="User names updated successfully.",
            data=UserProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK
        )



