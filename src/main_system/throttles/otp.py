from rest_framework.exceptions import Throttled
from rest_framework.throttling import SimpleRateThrottle
import logging

logger = logging.getLogger('django')


class OTPThrottle(SimpleRateThrottle):
    scope = 'otp'

    def get_cache_key(self, request, view):
        ip = self.get_ident(request)
        email = request.data.get('email')

        if not email:
            return None # No email provided, no throttling
        # Use a combination of IP and email to create a unique key
        ident = f"{ip}:{email.lower()}"

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


    def throttle_failure(self):
        duration = self.wait()

        message = f"Too many OTP attempts. Try again in {duration} seconds."
        logger.warning("Throttling triggered for OTP: IP/email limit exceeded.")

        raise Throttled(detail=message, wait=duration)