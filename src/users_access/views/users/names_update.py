from rest_framework import status
from main_system.base.auth_api import AuthAPI
from users_access.serializers.users.create_user_success import UserSerializer
from users_access.services.user_service import UserService
from users_access.serializers.users.names_update import NamesUpdateSerializer


class UserNamesUpdateAPI(AuthAPI):
    serializer_class = NamesUpdateSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        service = UserService()
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')
        user = service.update_names(request.user, first_name, last_name)

        return self.api_response(
            message="User names updated successfully.",
            data=UserSerializer(user).data,
            status_code=status.HTTP_200_OK
        )



