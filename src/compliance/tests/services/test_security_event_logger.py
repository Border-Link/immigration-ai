"""
Tests for SecurityEventLogger.

Focus:
- Ensure event types are correct
- Ensure sanitization/truncation occurs
- Ensure correct log levels are used (warning vs error)
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone as dt_timezone


@pytest.mark.django_db
class TestSecurityEventLogger:
    def test_log_authentication_failure_truncates_email_and_sanitizes_metadata(self, security_event_logger):
        fixed_now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=dt_timezone.utc)
        with patch("compliance.services.security_event_logger.timezone.now", return_value=fixed_now), \
             patch("compliance.services.security_event_logger.logger") as logger:
            security_event_logger.log_authentication_failure(
                email="user@example.com",
                ip_address="127.0.0.1",
                reason="bad_password",
                metadata={"password": "supersecret", "note": "ok"},
            )

            assert logger.warning.called is True
            msg = logger.warning.call_args[0][0]
            assert "authentication_failure" in msg
            assert "user@***" in msg  # truncated for privacy
            assert "***REDACTED***" in msg  # password redacted
            assert fixed_now.isoformat() in msg

    def test_log_authorization_denial_uses_warning(self, security_event_logger):
        with patch("compliance.services.security_event_logger.logger") as logger:
            security_event_logger.log_authorization_denial(
                user_id="u1",
                resource_type="case",
                resource_id="c1",
                action="read",
                ip_address="10.0.0.1",
                metadata={"token": "abcdef0123456789"},
            )

            assert logger.warning.called is True
            msg = logger.warning.call_args[0][0]
            assert "authorization_denial" in msg
            assert "***REDACTED***" in msg  # token redacted

    def test_log_payment_security_event_prefixes_type(self, security_event_logger):
        with patch("compliance.services.security_event_logger.logger") as logger:
            security_event_logger.log_payment_security_event(
                event_type="amount_mismatch",
                payment_id="p1",
                case_id="c1",
                user_id="u1",
                amount=10.5,
                reason="mismatch",
                metadata={"api_key": "k123"},
            )

            assert logger.warning.called is True
            msg = logger.warning.call_args[0][0]
            assert "payment_security_amount_mismatch" in msg
            assert "***REDACTED***" in msg

    def test_log_suspicious_activity_uses_error(self, security_event_logger):
        with patch("compliance.services.security_event_logger.logger") as logger:
            security_event_logger.log_suspicious_activity(
                activity_type="bruteforce",
                user_id="u1",
                ip_address="1.2.3.4",
                description="many attempts",
                metadata={"authorization": "Bearer abc.def.ghi"},
            )

            assert logger.error.called is True
            msg = logger.error.call_args[0][0]
            assert "suspicious_activity" in msg
            assert "***REDACTED***" in msg

    def test_log_rate_limit_exceeded_uses_warning(self, security_event_logger):
        with patch("compliance.services.security_event_logger.logger") as logger:
            security_event_logger.log_rate_limit_exceeded(
                endpoint="/api/v1/compliances/audit-logs/",
                ip_address="1.2.3.4",
                user_id="u1",
                metadata={"note": "ok"},
            )

            assert logger.warning.called is True
            msg = logger.warning.call_args[0][0]
            assert "rate_limit_exceeded" in msg
            assert "/api/v1/compliances/audit-logs/" in msg

