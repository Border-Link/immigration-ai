from django.urls import path
from .views.user_settings.create import UserSettingsToggleAPI, Enable2FAAPIView
from .views.user_settings.details import UserSettingsListAPIView
from .views.users.create import UserRegistrationAPI
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
    UserProfileAvatarAPI,
    UserAvatarAPI,
    UserNamesUpdateAPI
)
from .views.country import (
    CountryListAPI,
    CountryDetailAPI,
    CountryJurisdictionsAPI,
    CountryWithStatesAPI,
    CountrySearchAPI,
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
from .views.admin import (
    UserAdminListAPI,
    UserAdminDetailAPI,
    UserAdminActivateAPI,
    UserAdminDeactivateAPI,
    UserProfileAdminListAPI,
    UserProfileAdminDetailAPI,
    UserSuspendAPI,
    UserUnsuspendAPI,
    UserVerifyAPI,
    BulkUserOperationAPI,
    AdminPasswordResetAPI,
    UserRoleManagementAPI,
    CountryActivateAPI,
    CountrySetJurisdictionAPI,
    StateProvinceActivateAPI,
    NotificationAdminListAPI,
    NotificationAdminBulkCreateAPI,
    NotificationAdminDeleteAPI,
    UserStatisticsAPI,
    UserActivityAPI,
)

app_name = "users_access"

urlpatterns = [
    # -----------------------------
    # Canonical API routes (mounted under `/api/` and `/api/v1/auth/`)
    # -----------------------------
    # Users
    path("users/register/", UserRegistrationAPI.as_view(), name="users-register"),
    path("users/login/", UserLoginAPIView.as_view(), name="users-login"),
    path("users/login/verify/<str:endpoint_token>/", TwoFactorVerificationAPIView.as_view(), name="users-two-factor-verify"),
    path("users/login/resend-2fa/<str:endpoint_token>/", ResendTwoFactorTokenAPIView.as_view(), name="users-resend-2fa"),
    path("users/logout/", LogoutViewAPI.as_view(), name="users-logout"),
    path("users/logout-all/", LogoutAllViewAPI.as_view(), name="users-logout-all"),
    path("users/forgot-password/", SendForgotPasswordOTPAPIView.as_view(), name="users-forgot-password"),
    path("users/forgot-password/verify/<str:endpoint_token>/", PasswordResetOTPVerificationAPIView.as_view(), name="users-forgot-password-verify"),
    path("users/forgot-password/reset/<str:endpoint_token>/", CreateNewPasswordTokenAPIView.as_view(), name="users-forgot-password-reset"),
    path("users/account/", UserAccountAPI.as_view(), name="users-account"),
    path("users/status/", UserStatusAPI.as_view(), name="users-status"),
    path("users/profile/", UserProfileAPI.as_view(), name="users-profile"),
    path("users/profile/avatar/", UserProfileAvatarAPI.as_view(), name="users-profile-avatar"),
    path("users/avatar/", UserAvatarAPI.as_view(), name="users-avatar"),
    path("users/names/", UserNamesUpdateAPI.as_view(), name="users-names"),
    path("users/password/update/", UserPasswordUpdateAPI.as_view(), name="users-password-update"),
    path("users/settings/", UserSettingsListAPIView.as_view(), name="users-settings"),
    path("users/settings/enable-2fa/", Enable2FAAPIView.as_view(), name="users-enable-2fa"),
    path("users/settings/<str:setting_name>/", UserSettingsToggleAPI.as_view(), name="users-settings-toggle"),

    # Countries
    path("countries/", CountryListAPI.as_view(), name="countries-list"),
    path("countries/jurisdictions/", CountryJurisdictionsAPI.as_view(), name="countries-jurisdictions"),
    path("countries/with-states/", CountryWithStatesAPI.as_view(), name="countries-with-states"),
    path("countries/search/", CountrySearchAPI.as_view(), name="countries-search"),
    path("countries/<uuid:id>/", CountryDetailAPI.as_view(), name="country-detail"),
    path("countries/<uuid:id>/update/", CountryUpdateAPI.as_view(), name="country-update"),
    path("countries/<uuid:id>/delete/", CountryDeleteAPI.as_view(), name="country-delete"),
    
    # States/Provinces
    path("states/country/<uuid:country_id>/", StateProvinceListAPI.as_view(), name="states-list"),
    path("states/", StateProvinceCreateAPI.as_view(), name="states-create-compat"),
    path("states/nomination-programs/", StateProvinceNominationProgramsAPI.as_view(), name="states-nomination-programs"),
    path("states/<uuid:id>/", StateProvinceDetailAPI.as_view(), name="state-detail"),
    path("states/<uuid:id>/update/", StateProvinceUpdateAPI.as_view(), name="state-update"),
    path("states/<uuid:id>/delete/", StateProvinceDeleteAPI.as_view(), name="state-delete"),
    
    # Notifications
    path("notifications/", NotificationListAPI.as_view(), name="notifications-list"),
    path("notifications/unread-count/", NotificationUnreadCountAPI.as_view(), name="notifications-unread-count"),
    path("notifications/mark-read/", NotificationMarkReadAPI.as_view(), name="notifications-mark-read"),
    path("notifications/<uuid:id>/", NotificationDetailAPI.as_view(), name="notification-detail"),
    
    # Admin endpoints (staff/superuser only)
    # User Management
    path("admin/users/", UserAdminListAPI.as_view(), name="admin-users-list"),
    path("admin/users/statistics/", UserStatisticsAPI.as_view(), name="admin-users-statistics"),
    path("admin/users/bulk-operation/", BulkUserOperationAPI.as_view(), name="admin-users-bulk-operation"),
    path("admin/users/<uuid:id>/", UserAdminDetailAPI.as_view(), name="admin-users-detail"),
    path("admin/users/<uuid:id>/activate/", UserAdminActivateAPI.as_view(), name="admin-users-activate"),
    path("admin/users/<uuid:id>/deactivate/", UserAdminDeactivateAPI.as_view(), name="admin-users-deactivate"),
    path("admin/users/<uuid:id>/suspend/", UserSuspendAPI.as_view(), name="admin-users-suspend"),
    path("admin/users/<uuid:id>/unsuspend/", UserUnsuspendAPI.as_view(), name="admin-users-unsuspend"),
    path("admin/users/<uuid:id>/verify/", UserVerifyAPI.as_view(), name="admin-users-verify"),
    path("admin/users/<uuid:id>/reset-password/", AdminPasswordResetAPI.as_view(), name="admin-users-reset-password"),
    path("admin/users/<uuid:id>/role/", UserRoleManagementAPI.as_view(), name="admin-users-role"),
    path("admin/users/<uuid:id>/activity/", UserActivityAPI.as_view(), name="admin-users-activity"),
    
    # User Profile Management
    path("admin/user-profiles/", UserProfileAdminListAPI.as_view(), name="admin-user-profiles-list"),
    path("admin/user-profiles/<uuid:user_id>/", UserProfileAdminDetailAPI.as_view(), name="admin-user-profiles-detail"),
    
    # Country Management
    path("admin/countries/<uuid:id>/activate/", CountryActivateAPI.as_view(), name="admin-countries-activate"),
    path("admin/countries/<uuid:id>/set-jurisdiction/", CountrySetJurisdictionAPI.as_view(), name="admin-countries-set-jurisdiction"),
    
    # State/Province Management
    path("admin/states/<uuid:id>/activate/", StateProvinceActivateAPI.as_view(), name="admin-states-activate"),
    
    # Notification Management
    path("admin/notifications/", NotificationAdminListAPI.as_view(), name="admin-notifications-list"),
    path("admin/notifications/bulk/", NotificationAdminBulkCreateAPI.as_view(), name="admin-notifications-bulk"),
    path("admin/notifications/<uuid:id>/delete/", NotificationAdminDeleteAPI.as_view(), name="admin-notifications-delete"),
]