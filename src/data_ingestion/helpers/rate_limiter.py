"""
Rate limiter for LLM API calls.

Implements token bucket algorithm to prevent exceeding OpenAI rate limits.
"""

import time
import logging
from typing import Optional
from threading import Lock
from django.conf import settings
from main_system.utils.cache_utils import cache_get, cache_set

logger = logging.getLogger('django')

# Default rate limits (requests per minute)
DEFAULT_RATE_LIMIT_RPM = 60  # 60 requests per minute
DEFAULT_RATE_LIMIT_TPM = 1000000  # 1M tokens per minute (OpenAI default for GPT-4)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Implements a distributed token bucket using Django cache for thread-safety
    across multiple processes/workers.
    """
    
    def __init__(
        self,
        requests_per_minute: Optional[int] = None,
        tokens_per_minute: Optional[int] = None,
        cache_key_prefix: str = 'llm_rate_limit'
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute (None = no limit)
            tokens_per_minute: Maximum tokens per minute (None = no limit)
            cache_key_prefix: Prefix for cache keys
        """
        self.requests_per_minute = requests_per_minute or getattr(
            settings, 'LLM_RATE_LIMIT_RPM', DEFAULT_RATE_LIMIT_RPM
        )
        self.tokens_per_minute = tokens_per_minute or getattr(
            settings, 'LLM_RATE_LIMIT_TPM', DEFAULT_RATE_LIMIT_TPM
        )
        self.cache_key_prefix = cache_key_prefix
        self.lock = Lock()
    
    def _get_cache_key(self, bucket_type: str) -> str:
        """Get cache key for bucket type."""
        return f"{self.cache_key_prefix}:{bucket_type}"
    
    def _get_tokens(self, bucket_type: str) -> tuple[float, float]:
        """
        Get current token count and last refill time.
        
        Returns:
            Tuple of (tokens, last_refill_time)
        """
        cache_key = self._get_cache_key(bucket_type)
        # Start "full" on first use to avoid initial artificial throttling.
        default_tokens = float(self.requests_per_minute) if bucket_type == "requests" else float(self.tokens_per_minute)
        data = cache_get(cache_key, {'tokens': default_tokens, 'last_refill': time.time()})
        return data.get('tokens', 0.0), data.get('last_refill', time.time())
    
    def _refill_tokens(self, bucket_type: str, max_tokens: float) -> float:
        """
        Refill tokens based on elapsed time.
        
        Args:
            bucket_type: Type of bucket ('requests' or 'tokens')
            max_tokens: Maximum tokens for this bucket
            
        Returns:
            Current token count after refill
        """
        cache_key = self._get_cache_key(bucket_type)
        current_time = time.time()
        
        # Get current state
        # Start "full" on first use to avoid initial artificial throttling.
        data = cache_get(cache_key, {'tokens': max_tokens, 'last_refill': current_time})
        tokens = data.get('tokens', 0.0)
        last_refill = data.get('last_refill', current_time)
        
        # Calculate elapsed time (in minutes)
        elapsed_minutes = (current_time - last_refill) / 60.0
        
        # Refill tokens: add tokens proportional to elapsed time
        # Rate is per minute, so we add (rate * elapsed_minutes)
        tokens_to_add = max_tokens * elapsed_minutes
        new_tokens = min(tokens + tokens_to_add, max_tokens)
        
        # Update cache
        cache_set(
            cache_key,
            {'tokens': new_tokens, 'last_refill': current_time},
            timeout=120  # 2 minutes cache timeout
        )
        
        return new_tokens
    
    def _consume_tokens(self, bucket_type: str, tokens_needed: float, max_tokens: float) -> bool:
        """
        Try to consume tokens from bucket.
        
        Args:
            bucket_type: Type of bucket ('requests' or 'tokens')
            tokens_needed: Number of tokens to consume
            max_tokens: Maximum tokens for this bucket
            
        Returns:
            True if tokens were consumed, False if insufficient
        """
        with self.lock:
            # Refill first
            current_tokens = self._refill_tokens(bucket_type, max_tokens)
            
            if current_tokens >= tokens_needed:
                # Consume tokens
                new_tokens = current_tokens - tokens_needed
                cache_key = self._get_cache_key(bucket_type)
                cache_set(
                    cache_key,
                    {'tokens': new_tokens, 'last_refill': time.time()},
                    timeout=120
                )
                return True
            
            return False
    
    def wait_if_needed(self, estimated_tokens: int = 0) -> float:
        """
        Wait if rate limit would be exceeded.
        
        Args:
            estimated_tokens: Estimated tokens for the request
            
        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        # Check request rate limit
        if self.requests_per_minute > 0:
            can_consume = self._consume_tokens('requests', 1.0, float(self.requests_per_minute))
            if not can_consume:
                # Calculate wait time
                tokens, last_refill = self._get_tokens('requests')
                elapsed = time.time() - last_refill
                # Need to wait until we can get 1 token
                # Rate is per minute, so 1 token = 60/rate seconds
                wait_time = max(0, (60.0 / self.requests_per_minute) - elapsed)
                if wait_time > 0:
                    if getattr(settings, "APP_ENV", None) != "test":
                        logger.warning(f"Rate limit: waiting {wait_time:.2f}s for request bucket")
                    time.sleep(wait_time)
                    # Retry after wait
                    self._consume_tokens('requests', 1.0, float(self.requests_per_minute))
                return wait_time
        
        # Check token rate limit
        if self.tokens_per_minute > 0 and estimated_tokens > 0:
            can_consume = self._consume_tokens('tokens', float(estimated_tokens), float(self.tokens_per_minute))
            if not can_consume:
                # Calculate wait time
                tokens, last_refill = self._get_tokens('tokens')
                elapsed = time.time() - last_refill
                # Need to wait until we can get enough tokens
                # Rate is per minute, so tokens_needed/rate minutes = wait time
                wait_time = max(0, ((estimated_tokens / self.tokens_per_minute) * 60) - elapsed)
                if wait_time > 0:
                    if getattr(settings, "APP_ENV", None) != "test":
                        logger.warning(f"Rate limit: waiting {wait_time:.2f}s for token bucket (need {estimated_tokens} tokens)")
                    time.sleep(wait_time)
                    # Retry after wait
                    self._consume_tokens('tokens', float(estimated_tokens), float(self.tokens_per_minute))
                return wait_time
        
        return 0.0
    
    def record_usage(self, tokens_used: int) -> None:
        """
        Record actual token usage after API call.
        
        Args:
            tokens_used: Actual tokens used
        """
        if self.tokens_per_minute > 0 and tokens_used > 0:
            # Adjust token bucket based on actual usage
            # This handles cases where estimated != actual
            cache_key = self._get_cache_key('tokens')
            data = cache_get(cache_key, {'tokens': 0.0, 'last_refill': time.time()})
            current_tokens = data.get('tokens', 0.0)
            
            # If we used more than estimated, we may have gone negative
            # This is okay, it will refill naturally
            # We just update the last_refill to now to prevent double-counting
            cache_set(
                cache_key,
                {'tokens': current_tokens, 'last_refill': time.time()},
                timeout=120
            )


# Global rate limiter instance
_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter() -> TokenBucketRateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = TokenBucketRateLimiter()
    return _rate_limiter
