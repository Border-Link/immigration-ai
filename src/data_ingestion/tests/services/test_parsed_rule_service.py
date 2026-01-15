"""
Tests for ParsedRuleService.
"""

import pytest


@pytest.mark.django_db
class TestParsedRuleService:
    def test_get_all(self, parsed_rule_service, parsed_rule):
        qs = parsed_rule_service.get_all()
        assert qs.count() >= 1

    def test_get_by_status(self, parsed_rule_service, parsed_rule):
        qs = parsed_rule_service.get_by_status("pending")
        assert qs.count() >= 1
        assert all(r.status == "pending" for r in qs)

    def test_get_by_visa_code(self, parsed_rule_service, parsed_rule):
        qs = parsed_rule_service.get_by_visa_code("UK_SKILLED_WORKER")
        assert qs.count() >= 1
        assert all(r.visa_code == "UK_SKILLED_WORKER" for r in qs)

    def test_get_pending(self, parsed_rule_service, parsed_rule):
        qs = parsed_rule_service.get_pending()
        assert qs.count() >= 1

    def test_get_by_id_success(self, parsed_rule_service, parsed_rule):
        found = parsed_rule_service.get_by_id(str(parsed_rule.id))
        assert found is not None
        assert str(found.id) == str(parsed_rule.id)

    def test_get_by_id_not_found(self, parsed_rule_service):
        found = parsed_rule_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_update_status_success(self, parsed_rule_service, parsed_rule):
        updated = parsed_rule_service.update_status(str(parsed_rule.id), "approved")
        assert updated is not None
        assert updated.status == "approved"

    def test_update_status_not_found(self, parsed_rule_service):
        updated = parsed_rule_service.update_status("00000000-0000-0000-0000-000000000000", "approved")
        assert updated is None

    def test_update_parsed_rule_fields(self, parsed_rule_service, parsed_rule):
        updated = parsed_rule_service.update_parsed_rule(str(parsed_rule.id), description="Updated description")
        assert updated is not None
        assert updated.description == "Updated description"

    def test_delete_parsed_rule_success(self, parsed_rule_service, parsed_rule):
        ok = parsed_rule_service.delete_parsed_rule(str(parsed_rule.id))
        assert ok is True
        assert parsed_rule_service.get_by_id(str(parsed_rule.id)) is None

    def test_delete_parsed_rule_not_found(self, parsed_rule_service):
        ok = parsed_rule_service.delete_parsed_rule("00000000-0000-0000-0000-000000000000")
        assert ok is False

    def test_get_by_filters(self, parsed_rule_service, parsed_rule):
        qs = parsed_rule_service.get_by_filters(status="pending", visa_code="UK_SKILLED_WORKER", min_confidence=0.5)
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, parsed_rule_service):
        stats = parsed_rule_service.get_statistics()
        assert isinstance(stats, dict)

