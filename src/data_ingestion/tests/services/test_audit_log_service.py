"""
Tests for RuleParsingAuditLogService.
"""

import pytest


@pytest.mark.django_db
class TestAuditLogService:
    def test_get_all(self, audit_log_service, audit_log):
        qs = audit_log_service.get_all()
        assert qs.count() >= 1

    def test_get_by_action(self, audit_log_service, audit_log):
        qs = audit_log_service.get_by_action("parse_started")
        assert qs.count() >= 1

    def test_get_by_status(self, audit_log_service, audit_log):
        qs = audit_log_service.get_by_status("success")
        assert qs.count() >= 1

    def test_get_by_error_type_empty(self, audit_log_service, audit_log):
        qs = audit_log_service.get_by_error_type("InsufficientTextError")
        assert qs.count() == 0

    def test_get_by_document_version(self, audit_log_service, document_version, audit_log):
        qs = audit_log_service.get_by_document_version(str(document_version.id))
        assert qs.count() >= 1

    def test_get_by_id_success(self, audit_log_service, audit_log):
        found = audit_log_service.get_by_id(str(audit_log.id))
        assert found is not None
        assert str(found.id) == str(audit_log.id)

    def test_get_by_id_not_found(self, audit_log_service):
        found = audit_log_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_get_by_filters(self, audit_log_service, audit_log, document_version, staff_user):
        qs = audit_log_service.get_by_filters(
            action="parse_started",
            status="success",
            user_id=str(staff_user.id),
            document_version_id=str(document_version.id),
        )
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, audit_log_service):
        stats = audit_log_service.get_statistics()
        assert isinstance(stats, dict)

