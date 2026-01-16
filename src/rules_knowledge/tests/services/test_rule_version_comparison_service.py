"""
Tests for RuleVersionComparisonService.
All tests use services for setup; no direct model calls from tests.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from rules_knowledge.services.rule_version_comparison_service import RuleVersionComparisonService
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService


@pytest.mark.django_db
class TestRuleVersionComparisonService:
    def test_compare_versions_added_removed_modified(self, visa_type_uk, document_type_service):
        # create two versions
        v1 = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() - timedelta(days=10),
            effective_to=timezone.now() - timedelta(days=5),
            is_published=False,
        )
        v2 = VisaRuleVersionService.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() - timedelta(days=4),
            effective_to=None,
            is_published=False,
        )

        # requirements: v1 has R1, v2 has R1 modified + R2 added
        VisaRequirementService.create_requirement(
            rule_version_id=str(v1.id),
            requirement_code="R1",
            rule_type="eligibility",
            description="Desc v1",
            condition_expression={"==": [{"var": "x"}, 1]},
            is_mandatory=True,
        )
        VisaRequirementService.create_requirement(
            rule_version_id=str(v2.id),
            requirement_code="R1",
            rule_type="eligibility",
            description="Desc v2",
            condition_expression={"==": [{"var": "x"}, 2]},
            is_mandatory=True,
        )
        VisaRequirementService.create_requirement(
            rule_version_id=str(v2.id),
            requirement_code="R2",
            rule_type="eligibility",
            description="New",
            condition_expression={"==": [1, 1]},
            is_mandatory=True,
        )

        # document requirements: v1 has DOC1 mandatory, v2 has DOC1 optional (modified) + DOC2 added
        doc1 = document_type_service.create_document_type(code="DOC1", name="Doc 1")
        doc2 = document_type_service.create_document_type(code="DOC2", name="Doc 2")
        VisaDocumentRequirementService.create_document_requirement(str(v1.id), str(doc1.id), mandatory=True, conditional_logic=None)
        VisaDocumentRequirementService.create_document_requirement(str(v2.id), str(doc1.id), mandatory=False, conditional_logic={"description": "changed"})
        VisaDocumentRequirementService.create_document_requirement(str(v2.id), str(doc2.id), mandatory=True, conditional_logic=None)

        out = RuleVersionComparisonService.compare_versions(str(v1.id), str(v2.id))
        assert "error" not in out

        assert out["summary"]["requirements_added"] == 1
        assert out["summary"]["requirements_removed"] == 0
        assert out["summary"]["requirements_modified"] == 1

        assert out["summary"]["document_requirements_added"] == 1
        assert out["summary"]["document_requirements_removed"] == 0
        assert out["summary"]["document_requirements_modified"] == 1

    def test_compare_versions_handles_exception(self):
        out = RuleVersionComparisonService.compare_versions("bad", "bad")
        assert "error" in out
        assert out["requirements"]["added"] == []

