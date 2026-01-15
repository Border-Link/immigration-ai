from django.utils import timezone
from users_access.models.otp import OTP


class OTPSelector:
    """Read-only OTP queries"""

    @staticmethod
    def get_by_otp_and_endpoint_token(otp, endpoint_token):
        return (
            OTP.objects
            .filter(otp=otp, endpoint_token=endpoint_token, is_verified=False, expires_at__gt=timezone.now())
            .last()
        )

    @staticmethod
    def get_by_endpoint(endpoint_token):
        # Return the latest OTP for an endpoint token (verified or not).
        # Callers that specifically want "active/unverified" should use `endpoint_token()`.
        return OTP.objects.filter(endpoint_token=endpoint_token).last()

    @staticmethod
    def endpoint_token(endpoint_token):
        otp = OTP.objects.filter(endpoint_token=endpoint_token, is_verified=False, expires_at__gt=timezone.now()).last()
        return otp

    @staticmethod
    def get_by_endpoint_and_user(endpoint_token, user):
        otp = OTP.objects.filter(endpoint_token=endpoint_token, user=user).last()
        return otp

    @staticmethod
    def get_last_unverified_otp(user):
        otp = OTP.objects.filter(user=user, is_verified=False, expires_at__gt=timezone.now()).last()
        return otp

    @staticmethod
    def get_expired_unverified():
        return OTP.objects.filter(is_verified=False, expires_at__lt=timezone.now())
