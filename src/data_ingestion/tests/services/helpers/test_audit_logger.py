import pytest

from data_ingestion.helpers.audit_logger import RuleParsingAuditLogger


@pytest.mark.django_db
class TestAuditLogger:
    def test_log_parse_started_creates_row(self, document_version):
        log = RuleParsingAuditLogger.log_parse_started(document_version, metadata={"x": 1})
        assert log is not None
        assert log.action == "parse_started"

    def test_log_parse_failed_creates_row(self, document_version):
        log = RuleParsingAuditLogger.log_parse_failed(document_version, error_type="TestError", error_message="boom")
        assert log is not None
        assert log.status == "failure"

