import pytest


@pytest.mark.django_db
class TestComplianceOptimisticLocking:
    def test_audit_log_update_version_conflict_returns_none(self, audit_log_service, make_audit_log):
        log = make_audit_log(level="INFO", logger_name="x", message="m")
        assert log.version == 1

        updated = audit_log_service.update_audit_log(str(log.id), version=999, message="changed")
        assert updated is None

    def test_audit_log_soft_delete_filters_out_from_selector_and_service(self, audit_log_service, make_audit_log):
        from compliance.selectors.audit_log_selector import AuditLogSelector

        log = make_audit_log(level="INFO", logger_name="x", message="m")
        assert AuditLogSelector.get_by_id(str(log.id)) is not None

        ok = audit_log_service.delete_audit_log(str(log.id), version=log.version)
        assert ok is True

        assert AuditLogSelector.get_by_id(str(log.id)) is None
        assert audit_log_service.get_by_id(str(log.id)) is None

