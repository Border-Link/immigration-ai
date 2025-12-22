from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.totp_issuer import QRCodeGenerator
from users_access.serializers.user_settings.setting_serializer import UserSettingSerializer
from users_access.services.user_setting_service import UserSettingsService


class UserSettingsListAPIView(AuthAPI):

    def get(self, request):
        user = request.user
        settings = UserSettingsService.get_settings(user)
        if not settings:
            return self.api_response(
                message="User settings not found.",
                data={},
                status_code=status.HTTP_200_OK
            )

        response = UserSettingSerializer(settings).data

        if settings and settings.two_factor_auth and settings.totp_secret:
            qr_base64 = QRCodeGenerator.generate(secret=settings.totp_secret, user_email=user.email)
            response['qr_code'] = qr_base64

        return self.api_response(
            message="User settings retrieved successfully.",
            data=response,
            status_code=status.HTTP_200_OK
        )