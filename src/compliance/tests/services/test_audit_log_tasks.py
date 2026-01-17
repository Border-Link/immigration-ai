"""
Tests for compliance.tasks.audit_log_tasks.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestAuditLogTasks:
    def test_archive_old_audit_logs_task_success(self):
        from compliance.tasks.audit_log_tasks import archive_old_audit_logs_task

        qs = MagicMock()
        qs.count.return_value = 7

        with patch("compliance.tasks.audit_log_tasks.AuditLogService.get_by_date_range", return_value=qs) as sel, \
             patch("compliance.tasks.audit_log_tasks.logger"):
            result = archive_old_audit_logs_task.apply().get()

            assert result["success"] is True
            assert result["logs_to_archive"] == 7
            assert "Found 7 logs" in result["message"]
            assert sel.called is True
            # Task uses open-ended end_date filtering (older than one year)
            assert sel.call_args.args[0] is None

    def test_archive_old_audit_logs_task_retries_on_failure(self):
        from compliance.tasks.audit_log_tasks import archive_old_audit_logs_task
        from celery.exceptions import Retry

        with patch("compliance.tasks.audit_log_tasks.AuditLogService.get_by_date_range", side_effect=Exception("boom")), \
             patch("compliance.tasks.audit_log_tasks.logger"):
            with pytest.raises(Retry):
                archive_old_audit_logs_task.apply(throw=True)

