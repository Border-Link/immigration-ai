from django.utils.deprecation import MiddlewareMixin
from users_access.services import UserDeviceSessionService
from ..cookies.manager import CookieManager
from django.conf import settings


ACCESS_COOKIE_NAME = getattr(settings, "ACCESS_COOKIE_NAME", "access_token")
SESSION_COOKIE_NAME = getattr(settings, "SESSION_COOKIE_NAME", "sessionid")
FINGERPRINT_COOKIE_NAME = getattr(settings, "FINGERPRINT_COOKIE_NAME", "fingerprint")


class DeviceSessionRefreshMiddleware(MiddlewareMixin):

    def process_request(self, request):
        cookie_mgr = CookieManager(request, None)

        access_token = cookie_mgr.get_cookie(key=ACCESS_COOKIE_NAME, sign=False)
        if access_token and "HTTP_AUTHORIZATION" not in request.META:
            request.META["HTTP_AUTHORIZATION"] = f"Token {access_token}"

        return None

    def process_response(self, request, response):
        cookie_mgr = CookieManager(request, response)

        session_id = cookie_mgr.get_cookie(key=SESSION_COOKIE_NAME, sign=False)
        access_token = cookie_mgr.get_cookie(key=ACCESS_COOKIE_NAME, sign=False)
        fingerprint = cookie_mgr.get_cookie(key=FINGERPRINT_COOKIE_NAME)

        if not all([access_token, fingerprint, session_id]):
            return response

        device_session = UserDeviceSessionService.get_by_session_id(session_id=session_id, fingerprint=fingerprint)
        if not device_session or device_session.revoked:
            cookie_mgr.expire_cookies_and_tokens(token_obj=access_token, device_session=device_session)
            return response

        # Validate fingerprint
        if fingerprint != device_session.fingerprint:
            cookie_mgr.expire_cookies_and_tokens(token_obj=access_token, device_session=device_session)
            return response

        # Mark device session active
        UserDeviceSessionService.mark_active(session_id=session_id)
        return response
