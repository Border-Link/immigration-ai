import logging
from knox.views import LogoutAllView as KnoxLogoutAllView
from knox.models import AuthToken
from main_system.cookies.manager import CookieManager
from users_access.services.user_device_session_service import UserDeviceSessionService

logger = logging.getLogger('django')


class BaseLogoutMixin:
    COOKIE_NAMES = ['access_token', 'refresh_token']

    def _revoke_tokens(self, request):
        try:
            UserDeviceSessionService.revoke_all_for_user(user=request.user)
            AuthToken.objects.filter(user=request.user).delete()
        except Exception as e:
            logger.exception(f"Failed to revoke tokens on logout: {e}")

    def _clear_cookies(self, request, response):
        cookie_mgr = CookieManager(request, response)
        cookie_mgr.expire_all_cookies()


class LogoutViewAPI(BaseLogoutMixin, KnoxLogoutAllView):
    def post(self, request, *args, **kwargs):
        self._revoke_tokens(request)
        response = super().post(request, *args, **kwargs)
        self._clear_cookies(request, response)
        return response


class LogoutAllViewAPI(BaseLogoutMixin, KnoxLogoutAllView):
    def post(self, request, *args, **kwargs):
        self._revoke_tokens(request)
        response = super().post(request, *args, **kwargs)
        self._clear_cookies(request, response)
        return response
