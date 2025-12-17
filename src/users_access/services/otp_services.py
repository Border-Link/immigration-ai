from users_access.repositories.otp_repository import OTPRepository
from users_access.selectors import OTPSelector
import logging

logger = logging.getLogger('django')


class OTPService:

    @staticmethod
    def create(user, otp, endpoint_token, otp_type):
        try:
            return OTPRepository.create_otp(user=user, otp=otp, endpoint_token=endpoint_token, otp_type=otp_type)
        except Exception as e:
            logger.error(f"Error creating OTP for user {user.email}: {e}")
            return None

    @staticmethod
    def resend_otp(otp_model, otp):
        try:
            return OTPRepository.resend_otp(otp_model=otp_model, otp=otp)
        except Exception as e:
            logger.error(f"Error creating resending OTP for user {otp_model.user.email}: {e}")
            return None

    @staticmethod
    def verify_otp(otp, endpoint_token):
        try:
            otp_model = OTPSelector.get_by_otp_and_endpoint_token(otp=otp, endpoint_token=endpoint_token)
            if not otp_model:
                logger.warning(f"OTP verification failed for endpoint token {endpoint_token}")
                return False
            OTPRepository.verify_otp(otp_model)
            return otp_model.user
        except Exception as e:
            logger.error(f"Error verifying OTP for endpoint token {endpoint_token}: {e}")
            return False

    @staticmethod
    def cleanup_expired_otp():
        try:
            expired_qs = OTPSelector.get_expired_unverified()
            return OTPRepository.cleanup_expired_otp(queryset=expired_qs)
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {e}")
            return None

    @staticmethod
    def endpoint_token(endpoint_token):
        try:
            return OTPSelector.get_by_endpoint(endpoint_token=endpoint_token)
        except Exception as e:
            logger.error(f"Error retrieving OTP by endpoint token {endpoint_token}: {e}")
            return None

    @staticmethod
    def get_by_endpoint(endpoint_token):
        try:
            return OTPSelector.get_by_endpoint(endpoint_token)
        except Exception as e:
            logger.error(f"Error retrieving OTP by endpoint token {endpoint_token}: {e}")
            return None

    @staticmethod
    def get_by_endpoint_and_user(endpoint_token, user):
        try:
            return OTPSelector.get_by_endpoint_and_user(endpoint_token, user)
        except Exception as e:
            logger.error(f"Error retrieving OTP by endpoint token {endpoint_token} and user {user.email}: {e}")
            return None

    @staticmethod
    def get_last_unverified_otp(user):
        try:
            return OTPSelector.get_last_unverified_otp(user)
        except Exception as e:
            logger.error(f"Error retrieving last unverified OTP for user {user.email}: {e}")
            return None
