"""
Tests for AuditLogService.

Constraints:
- Do not create/read models directly in tests; use services.
"""

import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestAuditLogService:
    def test_create_audit_log_success_tracks_metrics(self, audit_log_service):
        with patch("compliance.services.audit_log_service.track_audit_log_creation") as track:
            log = audit_log_service.create_audit_log(
                level="INFO",
                logger_name="unit.test",
                message="hello",
                pathname="x.py",
                lineno=1,
                func_name="f",
                process=1,
                thread="t",
            )

            assert log is not None
            assert log.level == "INFO"
            assert log.logger_name == "unit.test"
            assert log.message == "hello"
            track.assert_called()

    def test_create_audit_log_failure_returns_none(self, audit_log_service):
        with patch("compliance.services.audit_log_service.AuditLogRepository.create_audit_log", side_effect=Exception("boom")):
            log = audit_log_service.create_audit_log(level="INFO", logger_name="x", message="y")
            assert log is None

    def test_get_all_returns_queryset(self, audit_log_service, make_audit_log):
        make_audit_log(level="INFO", logger_name="a", message="m1")
        make_audit_log(level="ERROR", logger_name="b", message="m2")
        qs = audit_log_service.get_all()
        assert qs.count() >= 2

    def test_get_by_level_filters(self, audit_log_service, make_audit_log):
        make_audit_log(level="INFO", logger_name="a", message="m1")
        make_audit_log(level="ERROR", logger_name="a", message="m2")

        qs = audit_log_service.get_by_level("ERROR")
        assert qs.count() >= 1
        assert all(item.level == "ERROR" for item in qs)

    def test_get_by_logger_name_filters(self, audit_log_service, make_audit_log):
        make_audit_log(level="INFO", logger_name="l1", message="m1")
        make_audit_log(level="INFO", logger_name="l2", message="m2")

        qs = audit_log_service.get_by_logger_name("l2")
        assert qs.count() >= 1
        assert all(item.logger_name == "l2" for item in qs)

    def test_get_by_id_success(self, audit_log_service, make_audit_log):
        log = make_audit_log(level="INFO", logger_name="x", message="m")
        found = audit_log_service.get_by_id(str(log.id))
        assert found is not None
        assert str(found.id) == str(log.id)

    def test_get_by_id_not_found(self, audit_log_service):
        from uuid import uuid4

        found = audit_log_service.get_by_id(str(uuid4()))
        assert found is None

    def test_get_recent_respects_limit(self, audit_log_service, make_audit_log):
        for i in range(5):
            make_audit_log(level="INFO", logger_name="x", message=f"m{i}")

        qs = audit_log_service.get_recent(limit=3)
        assert qs.count() <= 3

    def test_get_by_date_range_success(self, audit_log_service, make_audit_log):
        # We can't control timestamps without touching models; validate functional behavior
        # by using a wide range that includes created entries.
        from django.utils import timezone
        from datetime import timedelta

        make_audit_log(level="INFO", logger_name="x", message="m")

        start = timezone.now() - timedelta(days=1)
        end = timezone.now() + timedelta(days=1)
        qs = audit_log_service.get_by_date_range(start, end)
        assert qs.count() >= 1

    def test_service_error_handling_returns_empty_queryset(self, audit_log_service):
        with patch("compliance.services.audit_log_service.AuditLogSelector.get_all", side_effect=Exception("boom")):
            qs = audit_log_service.get_all()
            assert qs.count() == 0

