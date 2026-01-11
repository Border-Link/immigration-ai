from rest_framework import status
from rest_framework.permissions import AllowAny
from main_system.base.guest_api import GuestAPI
from main_system.throttles.otp import OTPThrottle
from users_access.services.otp_services import OTPService
from users_access.services.password_reset_services import PasswordResetService
from users_access.serializers.users.login import TwoFactorVerifySerializer
from users_access.serializers.users.password_reset_serializer import PasswordResetSerializer
from users_access.services.user_service import UserService
from users_access.serializers.users.reset_password_serializer import ResetPasswordSerializer
from users_access.helpers.otp_base import OTPBaseHandler
import logging



logger = logging.getLogger('django')

OTP_TYPE = 'password_reset'
MSG_INVALID_OTP = "Invalid or expired OTP."
MSG_PASSWORD_UPDATED = "Password updated successfully."
MSG_OTP_SENT = "OTP sent successfully."
OTP_VERIFIED_SUCCESSFULLY = "OTP verified successfully."

class SendForgotPasswordOTPAPIView(GuestAPI):

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["email"]

        otp_handler = OTPBaseHandler(otp_type=OTP_TYPE)
        _, endpoint_token = otp_handler.generate_and_send_otp(user=user)

        return self.api_response(
            message="OTP resent successfully",
            data={
                "email": user.email,
                "endpoint_token": endpoint_token
            },
            status_code=status.HTTP_200_OK
        )


class PasswordResetOTPVerificationAPIView(GuestAPI):
    permission_classes = (AllowAny,)
    serializer_class = TwoFactorVerifySerializer
    throttle_classes = [OTPThrottle]

    def post(self, request, endpoint_token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data.get('otp')

        user = OTPService.verify_otp(otp=otp, endpoint_token=endpoint_token)
        if not user:
            logger.error(f"Invalid or expired OTP for endpoint token {endpoint_token}")
            return self.api_response(
                message=MSG_INVALID_OTP,
                data={},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message=OTP_VERIFIED_SUCCESSFULLY,
            data={
                'email': user.email,
                'can_reset': True,
                'endpoint_token': endpoint_token
            },
            status_code=status.HTTP_200_OK
        )


class CreateNewPasswordTokenAPIView(GuestAPI):
    serializer_class = ResetPasswordSerializer

    def post(self, request, endpoint_token):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']
        user = serializer.validated_data['email']

        otp_entry = OTPService.get_by_endpoint_and_user(endpoint_token=endpoint_token, user=user)

        if not otp_entry:
            logger.error(
                f"Password reset failed. Invalid token or user mismatch. "
                f"Endpoint Token={endpoint_token}, User={user.email}"
            )

            return self.api_response(
                message="Invalid endpoint token or user.",
                data={},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        UserService.update_password(user, new_password)

        PasswordResetService.create_password_reset(user=user)

        logger.info(f"Password successfully updated for user={user.email}")

        return self.api_response(
            message="Password updated successfully.",
            data={'email': user.email},
            status_code=status.HTTP_200_OK
        )
