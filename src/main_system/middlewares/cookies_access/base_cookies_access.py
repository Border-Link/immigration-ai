from django.utils import timezone
from knox.auth import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from main_system.cookies.manager import CookieManager
from users_access.services.user_device_session_service import UserDeviceSessionService

ACCESS_COOKIE_NAME = "access_token"
SESSION_COOKIE_NAME = "sessionid"
FINGERPRINT_COOKIE_NAME = "fingerprint"


class BaseCookieAccessTokenAuthentication:

    @staticmethod
    def validate_token_and_device(request, require_session=True):
        """
        Validates access token and device session.
        Returns (user, token_obj)
        """
        cookie_mgr = CookieManager(request, None)
        access_token = cookie_mgr.get_cookie(ACCESS_COOKIE_NAME, sign=False)
        fingerprint = cookie_mgr.get_cookie(FINGERPRINT_COOKIE_NAME)
        session_id = cookie_mgr.get_cookie(SESSION_COOKIE_NAME, sign=False) if require_session else None

        if not access_token or not fingerprint or (require_session and not session_id):
            return None

        # Validate token
        auth = TokenAuthentication()
        user, token_obj = auth.authenticate_credentials(access_token.encode())
        if not user.is_active:
            raise AuthenticationFailed("User inactive")
        if token_obj.expiry and token_obj.expiry < timezone.now():
            raise AuthenticationFailed("Token expired")

        # Validate device session (only for prod)
        if require_session:
            device_session = UserDeviceSessionService.get_by_session_id(session_id=session_id, fingerprint=fingerprint)
            if not device_session or device_session.revoked:
                raise AuthenticationFailed("Invalid or revoked session")
            if device_session.user_id != user.id or device_session.fingerprint != fingerprint:
                raise AuthenticationFailed("Fingerprint/session mismatch")

        return user, token_obj
