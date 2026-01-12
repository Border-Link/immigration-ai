from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from main_system.utils.totp_issuer import QRCodeGenerator
from users_access.services.user_setting_service import UserSettingsService
from .user_settings import valid_fields



class UserSettingsToggleAPI(AuthAPI):
    permission_classes = [AuthenticationPermission]

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

        updated_settings = UserSettingsService.update_settings(
            request.user, {setting_name: value}
        )

        return self.api_response(
            message=f"{setting_name} updated successfully.",
            data={
                setting_name: getattr(updated_settings, setting_name)
            },
            status_code=status.HTTP_200_OK
        )


class Enable2FAAPIView(AuthAPI):
    permission_classes = [AuthenticationPermission]

    def post(self, request):
        user = request.user
        settings = UserSettingsService.enable_2fa(user)

        qr_base64 = QRCodeGenerator.generate(secret=settings.totp_secret, user_email=user.email)
        return self.api_response(
            message="2FA enabled successfully.",
            data={
                "qr_code": qr_base64
            },
            status=status.HTTP_200_OK
        )
