from django.db import transaction
from django.utils import timezone
from users_access.models.otp import OTP


class OTPRepository:

    @staticmethod
    def create_otp(user, otp, endpoint_token, otp_type):
        with transaction.atomic():
            expires_at = timezone.now() + timezone.timedelta(minutes=10)

            otp_data = OTP(
                user=user,
                otp=otp,
                endpoint_token=endpoint_token,
                type=otp_type,
                expires_at=expires_at,
                is_verified=False,
            )
            otp_data.full_clean()
            otp_data.save()

            return otp_data

    @staticmethod
    def resend_otp(otp_model, otp):
        with transaction.atomic():
            otp_model.otp = otp
            otp_model.expires_at = timezone.now() + timezone.timedelta(minutes=10)
            otp_model.is_verified = False

            otp_model.full_clean()
            otp_model.save()

            return otp_model

    @staticmethod
    def verify_otp(otp_model):
        with transaction.atomic():
            otp_model.is_verified = True
            otp_model.full_clean()
            otp_model.save()
            return otp_model

    @staticmethod
    def cleanup_expired_otp(queryset):
        count = queryset.count()
        queryset.delete()
        return count
