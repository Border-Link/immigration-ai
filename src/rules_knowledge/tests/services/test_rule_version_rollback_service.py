"""
Tests for RuleVersionRollbackService.
All tests use services/selectors; no direct model access from tests.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from rules_knowledge.services.rule_version_rollback_service import RuleVersionRollbackService
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector


@pytest.mark.django_db
class TestRuleVersionRollbackService:
    def test_rollback_validates_same_visa_type(self, visa_type_uk, visa_type_us):
        v1 = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() - timedelta(days=10),
            effective_to=None,
            is_published=True,
        )
        v2 = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_us.id),
            effective_from=timezone.now() - timedelta(days=5),
            effective_to=None,
            is_published=True,
        )
        out = RuleVersionRollbackService.rollback_to_version(str(v1.id), str(v2.id))
        assert out["success"] is False
        assert "same visa type" in out["error"].lower()

    def test_rollback_reopens_deleted_previous_and_closes_current(self, visa_type_uk, admin_user):
        # Create previous and current
        prev = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() - timedelta(days=10),
            effective_to=None,
            is_published=False,
        )
        prev = VisaRuleVersionService.publish_rule_version(str(prev.id))

        curr = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() - timedelta(days=1),
            effective_to=None,
            is_published=False,
        )
        curr = VisaRuleVersionService.publish_rule_version(str(curr.id))

        # Soft-delete previous to force reopen
        VisaRuleVersionService.delete_rule_version(str(prev.id))

        out = RuleVersionRollbackService.rollback_to_version(str(curr.id), str(prev.id), rollback_by=admin_user)
        assert out["success"] is True

        # Verify previous is accessible again and current is closed
        reopened = VisaRuleVersionService.get_by_id(str(prev.id))
        assert reopened is not None
        assert reopened.is_deleted is False
        assert reopened.is_published is True
        assert reopened.effective_to is None

        current_after = VisaRuleVersionService.get_by_id(str(curr.id))
        assert current_after is not None
        assert current_after.effective_to is not None

    def test_rollback_not_found(self):
        from uuid import uuid4

        out = RuleVersionRollbackService.rollback_to_version(str(uuid4()), str(uuid4()))
        assert out["success"] is False
        assert "not found" in out["error"].lower()

