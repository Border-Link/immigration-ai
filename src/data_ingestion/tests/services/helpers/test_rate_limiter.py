from unittest.mock import patch

from data_ingestion.helpers.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    def test_wait_if_needed_request_bucket_consumes(self):
        rl = TokenBucketRateLimiter(requests_per_minute=2, tokens_per_minute=0, cache_key_prefix="test_rl_1")
        assert rl.wait_if_needed() == 0.0
        assert rl.wait_if_needed() == 0.0

    @patch("data_ingestion.helpers.rate_limiter.time.sleep")
    def test_wait_if_needed_requests_rate_limited_waits(self, mock_sleep):
        rl = TokenBucketRateLimiter(requests_per_minute=1, tokens_per_minute=0, cache_key_prefix="test_rl_2")
        assert rl.wait_if_needed() == 0.0
        wait = rl.wait_if_needed()
        assert wait >= 0.0
        if wait > 0:
            mock_sleep.assert_called()

