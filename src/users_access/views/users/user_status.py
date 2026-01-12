from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.serializers.users.create_user_success import WhoAmISerializer


class UserStatusAPI(AuthAPI):
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return self.api_response(
                message="User is not authenticated.",
                data={},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        return self.api_response(
            message="User found successfully.",
            data=WhoAmISerializer(user).data,
            status_code=status.HTTP_200_OK
        )
