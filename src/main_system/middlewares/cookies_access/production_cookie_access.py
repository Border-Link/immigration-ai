from knox.auth import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils import timezone
from main_system.cookies.manager import CookieManager
from users_access.services.user_device_session_service import UserDeviceSessionService

ACCESS_COOKIE_NAME = getattr(settings, "ACCESS_COOKIE_NAME", "access_token")
SESSION_COOKIE_NAME = getattr(settings, "SESSION_COOKIE_NAME", "sessionid")
FINGERPRINT_COOKIE_NAME = getattr(settings, "FINGERPRINT_COOKIE_NAME", "fingerprint")
MFA_VERIFIED_COOKIE_NAME = getattr(settings, "MFA_VERIFIED_COOKIE_NAME", "mfa_verified")

class ProductionCookieAccessTokenAuthentication:

    def authenticate(self, request):


        cookie_mgr = CookieManager(request, None)

        access_token = cookie_mgr.get_cookie(key=ACCESS_COOKIE_NAME, sign=False)
        session_id = cookie_mgr.get_cookie(key=SESSION_COOKIE_NAME, sign=False)
        fingerprint = cookie_mgr.get_cookie(key=FINGERPRINT_COOKIE_NAME)


        if not all([access_token, session_id, fingerprint]):
            return None

        user, token_obj = TokenAuthentication().authenticate_credentials(access_token.encode())
        if not user.is_active:
            raise AuthenticationFailed("User does not exist please try again")

        if token_obj.expiry and token_obj.expiry < timezone.now():
            raise AuthenticationFailed("Token expired")

        device_session = UserDeviceSessionService.get_by_session_id(session_id=session_id, fingerprint=fingerprint)
        if not device_session or device_session.revoked:
            raise AuthenticationFailed("Invalid or revoked session")

        if device_session.user_id != user.id or device_session.fingerprint != fingerprint:
            raise AuthenticationFailed("Fingerprint/session mismatch")

        return user, token_obj