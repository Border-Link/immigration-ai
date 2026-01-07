from datetime import timedelta
import hashlib
import logging
from django.utils import timezone
from django.db import models
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from helpers.totp import TOTPAuthenticator
from users_access.services.otp_services import OTPService
from main_system.cookies.manager import CookieManager
from users_access.serializers.users.login import TwoFactorVerifySerializer

logger = logging.getLogger('django')

ACCESS_TOKEN_TTL_MINUTES = 24 * 60 * 60  # 24 hours
OTP_TYPE = 'login'


class TwoFactorVerificationAPIView(KnoxLoginView):
    permission_classes = (AllowAny,)
    serializer_class = TwoFactorVerifySerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            endpoint_token = self.kwargs.get('endpoint_token')
            otp = serializer.validated_data.get('otp')
            is_2fa = serializer.validated_data.get('is_2fa')

            user = self._verify_otp_or_2fa(endpoint_token, otp, is_2fa)
            if not user:
                return self._invalid_response()

            self._update_user_login_info(user)

            # Create access token
            access_token = self._create_access_token(user)

            # Generate or fetch device session
            device_session = self._create_device_session(user, request)

            # Build response with secure cookies
            response = self._build_response(user, access_token, device_session.fingerprint, is_2fa, request)

            logger.info(f"User {user.email} logged in successfully via 2FA/OTP")
            return response

        except Exception as e:
            logger.exception(f"Error during two-factor verification: {e}")
            return self._invalid_response()

    # ---------- Internal Helpers ----------

    def _verify_otp_or_2fa(self, endpoint_token, otp, is_2fa):
        if is_2fa:
            login_otp = OTPService.get_by_endpoint(endpoint_token=endpoint_token)
            if not login_otp:
                return None
            user = login_otp.user
            secret = getattr(user.user_settings, 'totp_secret', None)
            if not secret or not TOTPAuthenticator.verify_totp(secret=secret, otp=otp, valid_window=1):
                return None
        else:
            user = OTPService.verify_otp(otp=otp, endpoint_token=endpoint_token)
        return user

    def _update_user_login_info(self, user):
        user.login_count = models.F('login_count') + 1
        if not user.is_verified:
            user.is_verified = True
        user.last_login = timezone.now()
        user.save(update_fields=['login_count', 'is_verified', 'last_login'])

    def _create_access_token(self, user):
        _, access_token = AuthToken.objects.create(
            user,
            expiry=timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
        )
        return access_token

    def _create_device_session(self, user, request):
        # Flush the old session (deletes old session key and creates new one)
        request.session.flush()
        session_key = self._ensure_session(request=request)

        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        fingerprint_raw = f"{ip_address}|{user_agent}"
        fingerprint_hash = hashlib.sha256(fingerprint_raw.encode()).hexdigest()

        device_info = {
            "user_agent": user_agent,
            "ip_address": ip_address,
            "platform": request.META.get("HTTP_SEC_CH_UA_PLATFORM", ""),
            "browser": request.META.get("HTTP_SEC_CH_UA", ""),
            "accept_language": request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
        }

        # Ensure previous device session for same fingerprint is removed
        from users_access.services.user_device_session_service import UserDeviceSessionService
        UserDeviceSessionService.delete_by_fingerprint(user, fingerprint_hash)

        return UserDeviceSessionService.create_device_session(
            user=user,
            fingerprint=fingerprint_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            session_id=session_key,
            last_active=timezone.now()
        )

    def _ensure_session(self, request):
        """
        Ensure the request has a session and return the session_key.
        """
        if not request.session.session_key:
            request.session.create()
            request.session.save()
        return request.session.session_key


    def _build_response(self, user, access_token, fingerprint_hash, is_2fa, request):
        # Ensure session exists first
        if not request.session.session_key:
            request.session.create()

        request.session.save()
        session_id = request.session.session_key

        # Create response AFTER session exists
        response = Response()

        cookie_mgr = CookieManager(request, response)

        # Set all cookies together
        cookie_mgr.set_access_token(access_token)
        cookie_mgr.set_fingerprint(fingerprint_hash)
        if is_2fa:
            cookie_mgr.set_mfa_verified()
        cookie_mgr.set_last_active()
        cookie_mgr.set_session_id(session_id)  # session cookie last, but everything in same Response

        response.data = {
            "access_granted": True,
            "user": {"id": user.id, "email": user.email},
        }
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _invalid_response(self):
        return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

