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
from .views.user_profile import (
    UserProfileAPI,
    UserProfileAvatarAPI
)
from .views.country import (
    CountryListAPI,
    CountryDetailAPI,
    CountryJurisdictionsAPI,
    CountryWithStatesAPI,
    CountrySearchAPI,
    CountryCreateAPI,
    CountryUpdateAPI,
    CountryDeleteAPI
)
from .views.state_province import (
    StateProvinceListAPI,
    StateProvinceDetailAPI,
    StateProvinceNominationProgramsAPI,
    StateProvinceCreateAPI,
    StateProvinceUpdateAPI,
    StateProvinceDeleteAPI
)
from .views.notification import (
    NotificationListAPI,
    NotificationDetailAPI,
    NotificationUnreadCountAPI,
    NotificationMarkReadAPI
)

app_name = "user_access"

urlpatterns = [
    # User Authentication
    path("register/", UserRegistrationAPI.as_view(), name="register"),
    path("login/", UserLoginAPIView.as_view(), name="login"),
    path("login/verify/<str:endpoint_token>/", TwoFactorVerificationAPIView.as_view(), name='two-factor-verify'),
    path("resend-token/<str:endpoint_token>/", ResendTwoFactorTokenAPIView.as_view(), name='resent-two-factor-token'),
    path("logout/", LogoutViewAPI.as_view(), name="logout"),
    path("logoutall/", LogoutAllViewAPI.as_view(), name="logout-all"),
    
    # User Profile
    path("profile/", UserProfileAPI.as_view(), name="profile"),
    path("profile/avatar/", UserProfileAvatarAPI.as_view(), name="profile-avatar-delete"),
    
    # User Management (Legacy - keeping for backward compatibility)
    path("change-avatar/", UserAvatarAPI.as_view(), name="change-avatar"),
    path("change-names/", UserNamesUpdateAPI.as_view(), name="change-names"),
    path("change-password/", UserPasswordUpdateAPI.as_view(), name="change-password"),
    path("user-account/", UserAccountAPI.as_view(), name="user-account"),
    
    # Password Reset
    path("forgot-password/", SendForgotPasswordOTPAPIView.as_view(), name="forgot-password"),
    path("forgot-password/verify/<str:endpoint_token>/", PasswordResetOTPVerificationAPIView.as_view(), name="forgot-password-verify"),
    path("create-new-password/<str:endpoint_token>/", CreateNewPasswordTokenAPIView.as_view(), name="create-new-password"),
    
    # User Status
    path("whoami/", UserStatusAPI.as_view(), name="user-status"),
    
    # User Settings
    path('<str:setting_name>/create/', UserSettingsToggleAPI.as_view(), name='user_settings_toggle'),
    path('lists/config/', UserSettingsListAPIView.as_view(), name='config-lists'),
    path('enable-2fa/', Enable2FAAPIView.as_view(), name='enable-2fa'),
    
    # Countries
    path("countries/", CountryListAPI.as_view(), name="countries-list"),
    path("countries/create/", CountryCreateAPI.as_view(), name="countries-create"),
    path("countries/jurisdictions/", CountryJurisdictionsAPI.as_view(), name="countries-jurisdictions"),
    path("countries/with-states/", CountryWithStatesAPI.as_view(), name="countries-with-states"),
    path("countries/search/", CountrySearchAPI.as_view(), name="countries-search"),
    path("countries/<uuid:id>/", CountryDetailAPI.as_view(), name="country-detail"),
    path("countries/<uuid:id>/update/", CountryUpdateAPI.as_view(), name="country-update"),
    path("countries/<uuid:id>/delete/", CountryDeleteAPI.as_view(), name="country-delete"),
    
    # States/Provinces
    path("states/country/<uuid:country_id>/", StateProvinceListAPI.as_view(), name="states-list"),
    path("states/create/", StateProvinceCreateAPI.as_view(), name="states-create"),
    path("states/nomination-programs/", StateProvinceNominationProgramsAPI.as_view(), name="states-nomination-programs"),
    path("states/<uuid:id>/", StateProvinceDetailAPI.as_view(), name="state-detail"),
    path("states/<uuid:id>/update/", StateProvinceUpdateAPI.as_view(), name="state-update"),
    path("states/<uuid:id>/delete/", StateProvinceDeleteAPI.as_view(), name="state-delete"),
    
    # Notifications
    path("notifications/", NotificationListAPI.as_view(), name="notifications-list"),
    path("notifications/unread-count/", NotificationUnreadCountAPI.as_view(), name="notifications-unread-count"),
    path("notifications/mark-read/", NotificationMarkReadAPI.as_view(), name="notifications-mark-read"),
    path("notifications/<uuid:id>/", NotificationDetailAPI.as_view(), name="notification-detail"),
]