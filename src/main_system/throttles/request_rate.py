from rest_framework.throttling import SimpleRateThrottle
from rest_framework.exceptions import Throttled
import logging
import time

logger = logging.getLogger('django')

class RequestRateThrottle(SimpleRateThrottle):
    """
       General-purpose brute-force protection throttle.

       Usage:
           - Override `throttle_identifier_field` in your view to customize the unique identifier (email, token, etc.)
           - Scope is customizable per DRF settings
       """

    scope = 'request_rate'

    def get_cache_key(self, request, view):
        ip = self.get_ident(request=request)
        identifier = self.get_identifier(request, view)

        if not identifier:
            return None

        ident = f"{ip}:{identifier.lower()}"
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def get_identifier(self, request, view):
        field = getattr(view, 'throttle_identifier_field', 'email')
        return request.data.get(field) or request.query_params.get(field)


    def allow_request(self, request, view):
        self.key = self.get_cache_key(request=request, view=view)

        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        now = time.time()

        #remove old request
        self.history = [timestamp for timestamp in self.history if now - timestamp < self.duration]

        if len(self.history) >= self.num_requests:
            self.wait_time = self._calculate_backoff(len(self.history))
            logger.warning(f"Throttling triggered for {self.key}: {len(self.history)} requests in {self.duration} seconds.")
            self.throttle_failure()

        self.history.append(now)
        self.cache.set(self.key, self.history, self.duration)
        return True


    def throttle_failure(self):
        raise Throttled(
            detail=f"Too many attempts. Try again in {int(self.wait_time)} seconds.",
            wait=self.wait_time
        )

    def _calculate_backoff(self, attempt_count):
        base_wait = 600  # 10 minutes
        exponent = max(0, attempt_count - self.num_requests)
        backoff_time = base_wait * (2 ** exponent)
        return backoff_time

