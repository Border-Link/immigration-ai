from django.utils import timezone
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
import hashlib
import logging

logger = logging.getLogger("django")


salt_signer = f"{settings.SECRET_KEY}:{settings.ALLOWED_HOSTS}:{settings.DEBUG}-cookie-signer-v1"
hashed_salt = hashlib.sha256(str(salt_signer).encode('utf-8')).hexdigest()



class CookieManager:
    DEFAULTS = {
        "access_token_ttl_minutes": 24 * 60,  # 24 hours in minutes
        "fingerprint_ttl_days": 30,
        "mfa_verified_ttl_minutes": 15,
    }

    LIST_OF_COOKIES = [
        "access_token",
        "fingerprint",
        "mfa_verified",
        "last_active",
        "sessionid",
    ]

    APP_ENVIRONMENTS = ["local", "dev", "qa"]

    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.cookie_path = "/"
        self.samesite = "Lax" if settings.DEBUG else "Strict"
        self.domain = "localhost" if settings.DEBUG else ".borderlink.app"

        if settings.APP_ENV in self.APP_ENVIRONMENTS:
            self.samesite = "None"
            # Security: SameSite=None requires Secure=True (already set in set_cookie)
            # Verify secure is always True when SameSite=None
            if not settings.DEBUG:
                logger.warning("SameSite=None is set in non-debug environment. Ensure Secure=True.")


        self.signer = TimestampSigner(salt=hashed_salt)

    def set_cookie(self, key, value, max_age=None, sign=True):
        if value is None:
            logger.warning(f"Cookie {key} has None value. Skipping set_cookie.")
            return

        signed_value = self.signer.sign(str(value)) if sign else str(value)
        self.response.set_cookie(
            key=key,
            value=signed_value,
            max_age=max_age,
            path=self.cookie_path,
            httponly=True,
            secure=True,
            samesite=self.samesite,
            domain=self.domain,
        )


    def get_cookie(self, key, sign=True, max_age=None):
        val = self.request.COOKIES.get(key)
        allowed_age = max_age or 30 * 24 * 3600
        if val:
            if not sign:
                return val
            try:
                return self.signer.unsign(val, max_age=allowed_age)
            except SignatureExpired:
                logger.info(f"Cookie {key} signature expired (>{allowed_age} seconds)")
                return None
            except BadSignature:
                logger.warning(f"Cookie {key} has invalid signature mismatch.")
                return None
        return None

    def set_session_id(self, session_id, ttl_days=14):
        max_age = ttl_days * 24 * 3600
        self.set_cookie(key="sessionid", value=session_id, max_age=max_age, sign=False)

    def set_access_token(self, token, ttl_minutes=None):
        max_age = (ttl_minutes or self.DEFAULTS["access_token_ttl_minutes"]) * 60
        self.set_cookie(key="access_token", value=token, max_age=max_age, sign=False)

    def set_fingerprint(self, client_fingerprint, ttl_days=None):
        max_age = (ttl_days or self.DEFAULTS["fingerprint_ttl_days"]) * 24 * 3600
        if client_fingerprint:
            self.set_cookie(key="fingerprint", value=client_fingerprint, max_age=max_age)
        else:
            logger.warning("Fingerprint is None or empty. Skipping cookie set.")

    def set_mfa_verified(self, ttl_minutes=None):
        max_age = (ttl_minutes or self.DEFAULTS["mfa_verified_ttl_minutes"]) * 60
        self.set_cookie(key="mfa_verified", value="true", max_age=max_age)

    def set_last_active(self, timestamp=None):
        ts = timestamp or str(int(timezone.now().timestamp()))
        self.set_cookie(key="last_active", value=ts, max_age=30 * 24 * 3600)

    def expire_all_cookies(self):
        for cookie_name in self.LIST_OF_COOKIES:
            self.set_cookie(cookie_name, "", max_age=0, sign=False)

    def expire_cookies_and_tokens(self, token_obj=None, device_session=None):
        """
        Expire all cookies and optionally invalidate token and device session.
        """
        # 1. Expire cookies
        for cookie_name in self.LIST_OF_COOKIES:
            self.set_cookie(cookie_name, "", max_age=0, sign=False)
            logger.info(f"Expired cookie {cookie_name}.")

        # 2. Invalidate access token
        if token_obj:
            try:
                if isinstance(token_obj, str):
                    from knox.models import AuthToken
                    AuthToken.objects.filter(key=token_obj).delete()
                else:
                    from knox.models import AuthToken
                    AuthToken.objects.filter(digest=token_obj.digest).delete()
                    token_obj.expiry = timezone.now()
                    token_obj.save(update_fields=["expiry"])
                logger.info(f"Access token {token_obj.key} marked expired.")
            except Exception as e:
                logger.warning(f"Failed to expire token: {e}")

        # 3. Invalidate device session
        if device_session:
            try:
                from users_access.services.user_device_session_service import UserDeviceSessionService
                UserDeviceSessionService.revoke_session(session_id=device_session.session_id)
                logger.info(f"Device session {device_session.id} marked inactive.")
            except Exception as e:
                logger.warning(f"Failed to update device session: {e}")
