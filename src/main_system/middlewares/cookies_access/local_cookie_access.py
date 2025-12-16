from knox.auth import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils import timezone
from main_system.cookies.manager import CookieManager

ACCESS_COOKIE_NAME = getattr(settings, "ACCESS_COOKIE_NAME", "access_token")
FINGERPRINT_COOKIE_NAME = getattr(settings, "FINGERPRINT_COOKIE_NAME", "fingerprint")
MFA_VERIFIED_COOKIE_NAME = getattr(settings, "MFA_VERIFIED_COOKIE_NAME", "mfa_verified")

class LocalCookieAccessTokenAuthentication:

    def authenticate(self, request):

        cookie_mgr = CookieManager(request, None)
        access_token = cookie_mgr.get_cookie(key=ACCESS_COOKIE_NAME, sign=False)
        fingerprint = cookie_mgr.get_cookie(key=FINGERPRINT_COOKIE_NAME)

        if not all([access_token, fingerprint]):
            return None

        user, token_obj = TokenAuthentication().authenticate_credentials(access_token.encode())
        if not user.is_active:
            raise AuthenticationFailed("User does not exist please try again")

        if token_obj.expiry and token_obj.expiry < timezone.now():
            raise AuthenticationFailed("Token expired")

        return user, token_obj