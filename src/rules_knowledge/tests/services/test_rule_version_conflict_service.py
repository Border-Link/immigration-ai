"""
Tests for RuleVersionConflictService.
All tests use services for setup; no direct model calls from tests.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from rules_knowledge.services.rule_version_conflict_service import RuleVersionConflictService
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService


@pytest.mark.django_db
class TestRuleVersionConflictService:
    def test_detect_conflicts_and_can_create_version(self, visa_type_uk):
        existing = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() - timedelta(days=10),
            effective_to=None,
            is_published=True,
        )
        assert existing is not None

        new_from = timezone.now() - timedelta(days=5)
        new_to = timezone.now() + timedelta(days=5)

        conflicts = RuleVersionConflictService.detect_conflicts(str(visa_type_uk.id), new_from, new_to)
        assert len(conflicts) >= 1

        can_create, conflicts2 = RuleVersionConflictService.can_create_version(str(visa_type_uk.id), new_from, new_to)
        assert can_create is False
        assert len(conflicts2) >= 1

    def test_gap_analysis_smoke(self, visa_type_uk):
        # No versions -> full gap
        start = timezone.now() - timedelta(days=2)
        end = timezone.now()
        out = RuleVersionConflictService.get_gap_analysis(str(visa_type_uk.id), start, end)
        assert "coverage_percentage" in out
        assert out["total_gaps"] >= 1

