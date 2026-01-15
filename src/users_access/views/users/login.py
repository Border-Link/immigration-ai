import logging
from rest_framework import status
from main_system.base.guest_api import GuestAPI
from users_access.models.user_device_session import UserDeviceSession
from users_access.serializers.users.login import UserLoginSerializer
from users_access.helpers.otp_base import OTPBaseHandler
from users_access.services.user_device_session_service import UserDeviceSessionService
from knox.models import AuthToken

logger = logging.getLogger('django')
OTP_TYPE = 'login'

class UserLoginAPIView(GuestAPI):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        UserDeviceSessionService.revoke_all_for_user(user=user)
        AuthToken.objects.filter(user=user).delete()

        otp_handler = OTPBaseHandler(otp_type=OTP_TYPE)
        otp, endpoint_token = otp_handler.create_otp(user=user)

        user_settings = getattr(user, 'user_settings', None)
        if user_settings and user_settings.two_factor_auth:
            return self.api_response(
                message="Two-factor authentication is enabled. Please verify your identity.",
                data={
                    'email': user.email,
                    '2fa_enabled': True,
                    'endpoint_token': endpoint_token
                },
                status_code=status.HTTP_200_OK
            )

        otp_handler.send_otp_email(user=user, otp=otp)
        return self.api_response(
            message="OTP sent to your email",
            data={
                'email': user.email,
                '2fa_enabled': False,
                'endpoint_token': endpoint_token
            },
            status_code=status.HTTP_200_OK
        )
