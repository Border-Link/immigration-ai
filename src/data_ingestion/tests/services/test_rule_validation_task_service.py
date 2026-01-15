"""
Tests for RuleValidationTaskService.
"""

import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestRuleValidationTaskService:
    def test_get_all(self, rule_validation_task_service, validation_task):
        qs = rule_validation_task_service.get_all()
        assert qs.count() >= 1

    def test_get_by_status(self, rule_validation_task_service, validation_task):
        qs = rule_validation_task_service.get_by_status("pending")
        assert qs.count() >= 1
        assert all(t.status == "pending" for t in qs)

    def test_get_pending(self, rule_validation_task_service, validation_task):
        qs = rule_validation_task_service.get_pending()
        assert qs.count() >= 1

    def test_get_by_id_success(self, rule_validation_task_service, validation_task):
        found = rule_validation_task_service.get_by_id(str(validation_task.id))
        assert found is not None
        assert str(found.id) == str(validation_task.id)

    def test_get_by_id_not_found(self, rule_validation_task_service):
        found = rule_validation_task_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_assign_reviewer_success(self, rule_validation_task_service, validation_task, reviewer_user):
        updated = rule_validation_task_service.assign_reviewer(str(validation_task.id), str(reviewer_user.id))
        assert updated is not None
        assert updated.assigned_to_id == reviewer_user.id
        assert updated.status == "in_progress"

    def test_assign_reviewer_invalid_reviewer(self, rule_validation_task_service, validation_task):
        updated = rule_validation_task_service.assign_reviewer(str(validation_task.id), "00000000-0000-0000-0000-000000000000")
        assert updated is None

    def test_update_task_success(self, rule_validation_task_service, validation_task):
        updated = rule_validation_task_service.update_task(str(validation_task.id), status="needs_revision", reviewer_notes="Need more evidence")
        assert updated is not None
        assert updated.status == "needs_revision"
        assert updated.reviewer_notes == "Need more evidence"

    @patch("rules_knowledge.services.rule_publishing_service.RulePublishingService.publish_approved_validation_task")
    def test_approve_task_success_updates_parsed_rule_and_attempts_publish(
        self, mock_publish, rule_validation_task_service, validation_task
    ):
        # Publishing failures must not fail approval.
        mock_publish.return_value = {"success": False, "error": "nope"}
        updated = rule_validation_task_service.approve_task(str(validation_task.id), reviewer_notes="LGTM", auto_publish=True)
        assert updated is not None
        assert updated.status == "approved"
        assert updated.reviewer_notes == "LGTM"
        updated.parsed_rule.refresh_from_db()
        assert updated.parsed_rule.status == "approved"

    def test_reject_task_success(self, rule_validation_task_service, validation_task):
        updated = rule_validation_task_service.reject_task(str(validation_task.id), reviewer_notes="Incorrect")
        assert updated is not None
        assert updated.status == "rejected"
        assert updated.reviewer_notes == "Incorrect"

    def test_delete_validation_task_success(self, rule_validation_task_service, validation_task):
        ok = rule_validation_task_service.delete_validation_task(str(validation_task.id))
        assert ok is True
        assert rule_validation_task_service.get_by_id(str(validation_task.id)) is None

    def test_delete_validation_task_not_found(self, rule_validation_task_service):
        ok = rule_validation_task_service.delete_validation_task("00000000-0000-0000-0000-000000000000")
        assert ok is False

    def test_get_by_filters(self, rule_validation_task_service, validation_task):
        qs = rule_validation_task_service.get_by_filters(status="pending")
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, rule_validation_task_service):
        stats = rule_validation_task_service.get_statistics()
        assert isinstance(stats, dict)

