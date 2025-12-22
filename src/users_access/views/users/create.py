from rest_framework import status
from main_system.base.guest_api import GuestAPI
from users_access.services.otp_services import OTPService
from users_access.serializers.users.create_user_success import UserSerializer
from users_access.services.user_service import UserService
from users_access.serializers.users.create_user import CreateUserSerializer
from users_access.helpers.otp_base import OTPBaseHandler
import logging

logger = logging.getLogger('django')

OTP_TYPE = 'registration'

class UserRegistrationAPI(GuestAPI):
    serializer_class = CreateUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')
        user = UserService.create_user(email, password, first_name.title() if first_name else None, last_name.title() if last_name else None)

        # Generate a unique token for the endpoint
        otp_handler = OTPBaseHandler(otp_type=OTP_TYPE)
        otp, endpoint_token = otp_handler.generate_and_send_otp(user=user)
        OTPService.create(user=user, otp=otp, endpoint_token=endpoint_token, otp_type=OTP_TYPE)

        return self.api_response(
            message="User created successfully. Please check your email for confirmation OTP",
            data={
                'user': UserSerializer(user).data,
                'endpoint_token': endpoint_token
            },
            status_code=status.HTTP_200_OK
        )