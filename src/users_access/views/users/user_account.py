from datetime import timedelta
from django.utils.timezone import localtime, now
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.user_profile_service import UserProfileService


class UserAccountAPI(AuthAPI):
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        user = request.user
        profile = UserProfileService.get_profile(user)

        # User Profile Information
        user_profile = {
            "user_id": str(user.id),
            "email": user.email,
            "first_name": profile.first_name if profile else None,
            "last_name": profile.last_name if profile else None,
            "full_name": self._get_full_name(profile) if profile else None,
            "avatar": profile.avatar.url if profile and profile.avatar else None,
            "date_of_birth": profile.date_of_birth.strftime("%Y-%m-%d") if profile and profile.date_of_birth else None,
            "nationality": profile.nationality.code if profile and profile.nationality else None,
            "nationality_name": profile.nationality.name if profile and profile.nationality else None,
            "state_province": profile.state_province.code if profile and profile.state_province else None,
            "state_province_name": profile.state_province.name if profile and profile.state_province else None,
            "email_verified": user.is_verified,
            "consent_given": profile.consent_given if profile else False,
            "consent_timestamp": self._format_datetime(
                profile.consent_timestamp) if profile and profile.consent_timestamp else None,
            "member_since": self._format_datetime(user.created_at),
            "profile_created_at": self._format_datetime(profile.created_at) if profile else None,
            "profile_updated_at": self._format_datetime(profile.updated_at) if profile else None,
            "last_login": self._format_datetime(user.last_login) if user.last_login else None,
            "profile_completion": self._calculate_profile_completion(profile, user),
        }
        # User Account Information
        user_account = {
            "user_id": str(user.id),
            "role": user.role,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "must_change_password": user.must_change_password,
            "account_created_at": self._format_datetime(user.created_at),
            "account_updated_at": self._format_datetime(user.updated_at),
            "account_age_days": (now() - user.created_at).days if user.created_at else None,
            "days_since_last_login": (now() - user.last_login).days if user.last_login else None,
        }

        # User Settings Information
        user_setting = getattr(user, 'user_settings', None)
        user_settings = {
            "two_factor_enabled": user_setting.two_factor_auth if user_setting else False,
            "language": user_setting.language if user_setting else 'en',
            "timezone": user_setting.timezone if user_setting else 'UTC',
            "dark_mode": user_setting.dark_mode if user_setting else False,
            "email_notifications": user_setting.email_notifications if user_setting else True,
            "sms_notifications": user_setting.sms_notifications if user_setting else True,
            "push_notifications": user_setting.push_notifications if user_setting else True,
            "notify_case_status_updates": user_setting.notify_case_status_updates if user_setting else True,
            "notify_eligibility_results": user_setting.notify_eligibility_results if user_setting else True,
            "notify_document_status": user_setting.notify_document_status if user_setting else True,
            "notify_missing_documents": user_setting.notify_missing_documents if user_setting else True,
            "notify_rule_changes": user_setting.notify_rule_changes if user_setting else True,
            "notify_review_updates": user_setting.notify_review_updates if user_setting else True,
            "data_sharing_consent": user_setting.data_sharing_consent if user_setting else False,
            "marketing_emails": user_setting.marketing_emails if user_setting else False,
        }

        # User Security Information
        user_security = {
            "two_factor_enabled": user_setting.two_factor_auth if user_setting else False,
            "account_active": user.is_active,
            "email_verified": user.is_verified,
            "total_logins": user.login_count,
            "has_usable_password": user.has_usable_password(),
            "must_change_password": user.must_change_password,
            "security_score": self._get_security_score(user),
        }

        user_overview = {
            "profile": user_profile,
            "account": user_account,
            "settings": user_settings,
            "security": user_security
        }

        return self.api_response(
            message="User account information retrieved successfully.",
            data=user_overview,
            email=user.email,  # tests expect `response.data["email"]`
            status_code=status.HTTP_200_OK
        )


    def _get_security_score(self, user):
        score = 0
        total = 100

        # 1. Email verified
        if user.is_verified:
            score += 25

        # 2. Has usable password
        if user.has_usable_password():
            score += 25

        # 3. Two-factor auth
        user_setting = getattr(user, 'user_settings', None)
        if user_setting and user_setting.two_factor_auth:
            score += 30

        # 4. Password updated in last 3 months (based on PasswordReset)
        from users_access.selectors.password_reset_selector import PasswordResetSelector
        last_reset = None
        last_reset = PasswordResetSelector.get_by_user(user)
        if last_reset and last_reset.created_at > now() - timedelta(days=90):
            score += 10

        # 5. Has logged in before
        if hasattr(user, 'login_count') and user.login_count > 0:
            score += 10

        return {
            "score": score,
            "max_score": total,
            "percentage": round((score / total) * 100),
            "level": self._get_security_level(score),
            "last_password_change": self._format_datetime(
                last_reset.created_at) if last_reset and last_reset.created_at else None
        }


    def _get_security_level(self, score):
        if score >= 85:
            return "High"
        elif score >= 60:
            return "Moderate"
        else:
            return "Low"


    def _format_datetime(self, dt):
        if dt:
            return localtime(dt).strftime("%Y-%m-%d %H:%M:%S")
        return None


    def _get_full_name(self, profile):
        """Get full name from profile."""
        if not profile:
            return None
        parts = [profile.first_name, profile.last_name]
        full_name = " ".join(filter(None, parts))
        return full_name if full_name else None


    def _calculate_profile_completion(self, profile, user):
        """Calculate profile completion percentage."""
        if not profile:
            return 0

        total_fields = 0
        completed_fields = 0

        # Required fields
        fields_to_check = [
            ('first_name', profile.first_name),
            ('last_name', profile.last_name),
            ('email', user.email),
            ('nationality', profile.nationality),
            ('date_of_birth', profile.date_of_birth),
            ('consent_given', profile.consent_given),
        ]

        for field_name, field_value in fields_to_check:
            total_fields += 1
            if field_value:
                completed_fields += 1

        if total_fields == 0:
            return 0

        return round((completed_fields / total_fields) * 100)
