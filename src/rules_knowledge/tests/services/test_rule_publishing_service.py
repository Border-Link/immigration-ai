"""
Tests for RulePublishingService.

This service integrates with multiple apps (data_ingestion, ai_decisions, users_access).
For production-grade unit tests we mock cross-app selectors/repositories and focus on:
- control flow correctness
- error handling
- deterministic outputs
"""

from unittest.mock import patch, MagicMock

import pytest

from rules_knowledge.services.rule_publishing_service import RulePublishingService


@pytest.mark.django_db
class TestRulePublishingService:
    def test_publish_parsed_rule_not_found(self):
        with patch("rules_knowledge.services.rule_publishing_service.ParsedRuleSelector.get_by_id", return_value=None):
            out = RulePublishingService.publish_approved_parsed_rule("missing-id")
            assert out["success"] is False
            assert "not found" in out["error"].lower()

    def test_publish_parsed_rule_wrong_status(self):
        parsed = MagicMock()
        parsed.id = "pid"
        parsed.status = "pending"
        with patch("rules_knowledge.services.rule_publishing_service.ParsedRuleSelector.get_by_id", return_value=parsed):
            out = RulePublishingService.publish_approved_parsed_rule("pid")
            assert out["success"] is False
            assert "must be 'approved'" in out["error"]

    def test_publish_parsed_rule_success_happy_path(self):
        parsed = MagicMock()
        parsed.id = "pid"
        parsed.status = "approved"
        parsed.visa_code = "SKILLED_WORKER"
        parsed.rule_type = "eligibility"
        parsed.description = "desc"
        parsed.extracted_logic = {"==": [1, 1]}
        parsed.document_version = MagicMock()

        visa_type = MagicMock()
        visa_type.id = "vt"
        visa_type.jurisdiction = "UK"

        rule_version = MagicMock()
        rule_version.id = "rv"

        published_version = MagicMock()
        published_version.id = "rv"

        with (
            patch("rules_knowledge.services.rule_publishing_service.ParsedRuleSelector.get_by_id", return_value=parsed),
            patch.object(RulePublishingService, "_get_or_create_visa_type", return_value=visa_type),
            patch.object(RulePublishingService, "_create_rule_version", return_value=rule_version),
            patch.object(RulePublishingService, "_create_requirements_from_parsed_rule", return_value=1),
            patch.object(RulePublishingService, "_close_previous_version", return_value=True),
            patch("rules_knowledge.services.rule_publishing_service.VisaRuleVersionService.publish_rule_version", return_value=published_version),
            patch("data_ingestion.repositories.parsed_rule_repository.ParsedRuleRepository.update_parsed_rule", return_value=parsed),
            patch.object(RulePublishingService, "_notify_users_of_rule_change", return_value=None),
            patch.object(RulePublishingService, "_update_vector_db_for_document_version", return_value=None),
        ):
            out = RulePublishingService.publish_approved_parsed_rule("pid")
            assert out["success"] is True
            assert out["rule_version_id"] == "rv"
            assert out["requirements_created"] == 1
            assert out["previous_version_closed"] is True

    def test_create_requirements_from_parsed_rule_handles_structures(self):
        # Patch repository creation to avoid DB dependencies here
        with patch("rules_knowledge.services.rule_publishing_service.VisaRequirementRepository.create_requirement", return_value=object()):
            parsed = MagicMock()
            parsed.id = "pid"
            parsed.visa_code = "TEST"
            parsed.rule_type = "eligibility"
            parsed.description = "desc"

            rv = MagicMock()
            rv.id = "rv"

            # requirements array structure
            parsed.extracted_logic = {"requirements": [{"requirement_code": "A", "condition_expression": {"==": [1, 1]}}]}
            assert RulePublishingService._create_requirements_from_parsed_rule(rv, parsed) == 1

            # single requirement object
            parsed.extracted_logic = {"requirement_code": "B", "condition_expression": {"==": [1, 1]}, "description": "x"}
            assert RulePublishingService._create_requirements_from_parsed_rule(rv, parsed) == 1

            # direct expression dict
            parsed.extracted_logic = {"==": [1, 1]}
            assert RulePublishingService._create_requirements_from_parsed_rule(rv, parsed) == 1

            # list of requirement objects
            parsed.extracted_logic = [{"requirement_code": "C", "condition_expression": {"==": [1, 1]}}]
            assert RulePublishingService._create_requirements_from_parsed_rule(rv, parsed) == 1

