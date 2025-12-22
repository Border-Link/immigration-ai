from datetime import timedelta
from django.utils.timezone import localtime, now
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from users_access.models.password_reset import PasswordReset
from users_access.services.user_profile_service import UserProfileService

class UserAccountAPI(AuthAPI):

    def get(self, request):
        user = request.user
        profile = UserProfileService.get_profile(user)

        user_profile = {
            "first_name": profile.first_name if profile else None,
            "last_name": profile.last_name if profile else None,
            "email": user.email,
            "avatar": profile.avatar.url if profile and profile.avatar else None,
            "nationality": profile.nationality.code if profile and profile.nationality else None,
            "nationality_name": profile.nationality.name if profile and profile.nationality else None,
            "email_verified": user.is_verified,
            "member_since": self._format_datetime(user.created_at),
            "last_login": self._format_datetime(user.last_login) if user.last_login else None,
        }

        user_setting = getattr(user, 'user_settings', None)

        user_security = {
            "two_factor_enable": user_setting.two_factor_auth if user_setting else False,
            "account_active": user.is_active,
            "total_logins": user.login_count,
            "security_score": self._get_security_score(user),
        }

        user_overview = {
            "profile": user_profile,
            "security": user_security
        }

        return self.api_response(
            message="User password updated successfully.",
            data=user_overview,
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
        if getattr(user.user_settings, 'two_factor_auth', False):
            score += 30

        # 4. Password updated in last 3 months (based on PasswordReset)
        from users_access.selectors.password_reset_selector import PasswordResetSelector
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
            "last_password_change": last_reset.created_at if last_reset else None
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

