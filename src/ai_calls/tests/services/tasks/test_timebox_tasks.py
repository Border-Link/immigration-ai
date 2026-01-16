"""
Unit tests for Celery tasks in ai_calls.tasks.timebox_tasks.

These tests call the Celery Task `.run(...)` methods directly (no broker).
"""

import pytest
from unittest.mock import MagicMock


@pytest.mark.django_db
class TestTimeboxTasks:
    def test_enforce_timebox_task_success(self, monkeypatch):
        from ai_calls.tasks.timebox_tasks import enforce_timebox_task
        from ai_calls.services import timebox_service as timebox_service_module

        sentinel = object()
        monkeypatch.setattr(timebox_service_module.TimeboxService, "enforce_timebox", MagicMock(return_value=sentinel))

        res = enforce_timebox_task.run("session-1")
        assert res is sentinel

    def test_enforce_timebox_task_retries_on_exception(self, monkeypatch):
        from ai_calls.tasks.timebox_tasks import enforce_timebox_task
        from ai_calls.services import timebox_service as timebox_service_module

        class RetryRaised(Exception):
            pass

        monkeypatch.setattr(timebox_service_module.TimeboxService, "enforce_timebox", MagicMock(side_effect=Exception("boom")))

        # Configure retries and intercept retry() call.
        enforce_timebox_task.request.retries = 1
        monkeypatch.setattr(enforce_timebox_task, "retry", MagicMock(side_effect=RetryRaised()))

        with pytest.raises(RetryRaised):
            enforce_timebox_task.run("session-1")

        enforce_timebox_task.retry.assert_called()

    def test_send_timebox_warning_task_calls_service(self, monkeypatch):
        from ai_calls.tasks.timebox_tasks import send_timebox_warning_task
        from ai_calls.services import timebox_service as timebox_service_module

        monkeypatch.setattr(timebox_service_module.TimeboxService, "send_warning", MagicMock(return_value=True))

        send_timebox_warning_task.run("session-1", "5min")
        timebox_service_module.TimeboxService.send_warning.assert_called_once_with("session-1", "5min")

