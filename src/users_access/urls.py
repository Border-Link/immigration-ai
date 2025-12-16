from django.urls import path
from .views.user_settings.create import UserSettingsToggleAPI, Enable2FAAPIView
from .views.user_settings.details import UserSettingsListAPIView
from .views.users.avatar import UserAvatarAPI
from .views.users.create import UserRegistrationAPI
from .views.users.names_update import UserNamesUpdateAPI
from .views.users.password_update import UserPasswordUpdateAPI
from .views.users.user_account import UserAccountAPI
from .views.users.login import UserLoginAPIView
from .views.users.login_2fa import TwoFactorVerificationAPIView
from .views.users.resend_2fa import ResendTwoFactorTokenAPIView
from .views.users.forgot_password import (
    SendForgotPasswordOTPAPIView,
    PasswordResetOTPVerificationAPIView,
    CreateNewPasswordTokenAPIView
)

from .views.users.logout import (
    LogoutViewAPI,
    LogoutAllViewAPI
)
from .views.users.user_status import UserStatusAPI

app_name = "user_access"

urlpatterns = [
    path("register/", UserRegistrationAPI.as_view(), name="register"),
    path("login/", UserLoginAPIView.as_view(), name="login"),
    path("login/verify/<str:endpoint_token>/", TwoFactorVerificationAPIView.as_view(), name='two-factor-verify'),
    path("resend-token/<str:endpoint_token>/", ResendTwoFactorTokenAPIView.as_view(), name='resent-two-factor-token'),
    path("logout/", LogoutViewAPI.as_view(), name="logout"),
    path("logoutall/", LogoutAllViewAPI.as_view(), name="logout-all"),
    path("change-avatar/", UserAvatarAPI.as_view(), name="change-avatar"),
    path("change-names/", UserNamesUpdateAPI.as_view(), name="change-names"),
    path("change-password/", UserPasswordUpdateAPI.as_view(), name="change-password"),
    path("user-account/", UserAccountAPI.as_view(), name="user-account"),
    path("forgot-password/", SendForgotPasswordOTPAPIView.as_view(), name="forgot-password"),
    path("forgot-password/verify/<str:endpoint_token>/", PasswordResetOTPVerificationAPIView.as_view(), name="forgot-password-verify"),
    path("create-new-password/<str:endpoint_token>/", CreateNewPasswordTokenAPIView.as_view(), name="create-new-password"),
    path("whoami/", UserStatusAPI.as_view(), name="user-status"),
    path('<str:setting_name>/create/', UserSettingsToggleAPI.as_view(), name='user_settings_toggle'),
    path('lists/config/', UserSettingsListAPIView.as_view(), name='config-lists'),
    path('enable-2fa/', Enable2FAAPIView.as_view(), name='enable-2fa'),
]