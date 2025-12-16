from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.totp_issuer import QRCodeGenerator
from users_access.services.user_setting_service import UserSettingsService
from .user_settings import valid_fields



class UserSettingsToggleAPI(AuthAPI):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = UserSettingsService()


    def patch(self, request, setting_name):
        if setting_name not in valid_fields:
            return self.api_response(
                message="Invalid setting name",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        value = request.data.get("value")
        if value is None:
            return self.api_response(
                message="Value is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        updated_settings = self.service.update_settings(
            request.user.id, {setting_name: value}
        )

        return self.api_response(
            message=f"{setting_name} updated successfully.",
            data={
                setting_name: getattr(updated_settings, setting_name)
            },
            status_code=status.HTTP_200_OK
        )


class Enable2FAAPIView(AuthAPI):
    service = UserSettingsService()

    def post(self, request):
        user = request.user
        settings = self.service.enable_2fa(user_id=user.id)

        qr_base64 = QRCodeGenerator.generate(secret=settings.totp_secret, user_email=user.email)
        return self.api_response(
            message="2FA enabled successfully.",
            data={
                "qr_code": qr_base64
            },
            status=status.HTTP_200_OK
        )
