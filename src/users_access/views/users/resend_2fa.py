import logging
from django.utils.crypto import get_random_string
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from main_system.base.guest_api import GuestAPI
from main_system.throttles.otp import OTPThrottle
from helpers import fields as input_fields
from users_access.services.otp_services import OTPService
from users_access.tasks.otp_tasks import send_otp_email

logger = logging.getLogger('django')

class ResendTwoFactorTokenAPIView(GuestAPI):
    throttle_classes = [OTPThrottle]
    permission_classes = (AllowAny,)

    def post(self, request, endpoint_token):
        try:
            otp_service = OTPService()
            login_otp = otp_service.get_by_endpoint(endpoint_token=endpoint_token)
            if not login_otp:
                return self.api_response(
                    message="Invalid or expired endpoint token",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            otp = get_random_string(length=6, allowed_chars='0123456789')
            otp_service.resend_otp(otp_model=login_otp, otp=otp)

            # Get first_name from profile
            first_name = None
            if hasattr(login_otp.user, 'profile') and login_otp.user.profile:
                first_name = login_otp.user.profile.first_name

            send_otp_email.delay(login_otp.user.email, first_name, otp)
            return self.api_response(
                message="OTP resent successfully",
                data={"email": login_otp.user.email},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error during OTP resend: {e}")
            return Response({input_fields.ERROR: "Failed to resend OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
