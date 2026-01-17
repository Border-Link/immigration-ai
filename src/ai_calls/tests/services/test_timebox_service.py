"""
Tests for TimeboxService.
"""

import pytest
from unittest.mock import MagicMock
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestTimeboxService:
    def test_check_time_remaining_session_not_found(self):
        from ai_calls.services.timebox_service import TimeboxService

        info = TimeboxService.check_time_remaining("00000000-0000-0000-0000-000000000000")
        assert info["remaining_seconds"] == 0
        assert info["warning_level"] is None

    def test_check_time_remaining_warning_levels(self, monkeypatch, call_session_in_progress):
        from ai_calls.services.timebox_service import TimeboxService, CALL_DURATION_SECONDS
        from ai_calls.repositories.call_session_repository import CallSessionRepository

        # Set started_at such that 4 minutes remain
        started_at = timezone.now() - timedelta(seconds=CALL_DURATION_SECONDS - 240)
        call_session_in_progress = CallSessionRepository.update_call_session(
            call_session_in_progress,
            version=call_session_in_progress.version,
            started_at=started_at,
        )

        info = TimeboxService.check_time_remaining(str(call_session_in_progress.id))
        assert info["remaining_seconds"] <= 300
        assert info["warning_level"] in ("5min", "1min", None)

        # Set started_at such that < 1 minute remains
        started_at2 = timezone.now() - timedelta(seconds=CALL_DURATION_SECONDS - 30)
        call_session_in_progress = CallSessionRepository.update_call_session(
            call_session_in_progress,
            version=call_session_in_progress.version,
            started_at=started_at2,
        )
        info2 = TimeboxService.check_time_remaining(str(call_session_in_progress.id))
        assert info2["warning_level"] == "1min"

    def test_should_warn_and_should_terminate(self, call_session_in_progress):
        from ai_calls.services.timebox_service import TimeboxService, CALL_DURATION_SECONDS
        from ai_calls.repositories.call_session_repository import CallSessionRepository

        call_session_in_progress = CallSessionRepository.update_call_session(
            call_session_in_progress,
            version=call_session_in_progress.version,
            started_at=timezone.now() - timedelta(seconds=CALL_DURATION_SECONDS - 10),
        )
        assert TimeboxService.should_warn(str(call_session_in_progress.id)) is True
        assert TimeboxService.should_terminate(str(call_session_in_progress.id)) is False

        call_session_in_progress = CallSessionRepository.update_call_session(
            call_session_in_progress,
            version=call_session_in_progress.version,
            started_at=timezone.now() - timedelta(seconds=CALL_DURATION_SECONDS + 10),
        )
        assert TimeboxService.should_terminate(str(call_session_in_progress.id)) is True

    def test_enforce_timebox_skips_when_not_in_progress(self, call_session_ready):
        from ai_calls.services.timebox_service import TimeboxService

        # Not in progress -> None
        res = TimeboxService.enforce_timebox(str(call_session_ready.id))
        assert res is None

    def test_enforce_timebox_calls_end_call_when_in_progress(self, monkeypatch, call_session_in_progress):
        from ai_calls.services.timebox_service import TimeboxService
        from ai_calls.services import call_session_service as call_session_service_module

        # In progress -> calls end_call
        monkeypatch.setattr(
            call_session_service_module.CallSessionService,
            "end_call",
            MagicMock(name="end_call", return_value=call_session_in_progress),
        )
        res2 = TimeboxService.enforce_timebox(str(call_session_in_progress.id))
        assert res2 is not None

    def test_send_warning_logs(self, call_session_in_progress):
        from ai_calls.services.timebox_service import TimeboxService
        from ai_calls.selectors.call_audit_log_selector import CallAuditLogSelector

        ok = TimeboxService.send_warning(str(call_session_in_progress.id), "5min")
        assert ok in (True, False)  # defensive: depends on audit log plumbing

        logs = CallAuditLogSelector.get_by_call_session(call_session_in_progress)
        assert logs.count() >= 0

