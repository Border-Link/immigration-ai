"""
Focused tests for RuleParsingService.parse_document_version orchestration.
External dependencies (LLM, cache) are mocked.
"""

import pytest
from unittest.mock import patch

from data_ingestion.services.rule_parsing.service import RuleParsingService


@pytest.mark.django_db
class TestRuleParsingService:
    @patch("data_ingestion.services.rule_parsing.service.LLMHandler")
    def test_parse_document_version_success_creates_rules_and_tasks(self, mock_llm, document_version):
        mock_llm.call_llm_for_rule_extraction.return_value = {
            "success": True,
            "rules": [
                {
                    "visa_code": "UK_SKILLED_WORKER",
                    "requirement_code": "FEE_PAYMENT",
                    "description": "Applicant must pay the fee.",
                    "condition_expression": {"==": [{"var": "fee_paid"}, True]},
                    "source_excerpt": "Fee is required",
                }
            ],
            "model": "test",
            "usage": {"total_tokens": 12, "prompt_tokens": 6, "completion_tokens": 6},
            "estimated_cost": 0.01,
            "processing_time_ms": 5,
        }

        result = RuleParsingService.parse_document_version(document_version)
        assert result["success"] is True
        assert result["rules_created"] == 1
        assert result["validation_tasks_created"] == 1

    @patch("data_ingestion.services.rule_parsing.service.LLMHandler")
    def test_parse_document_version_llm_failure_returns_error(self, mock_llm, document_version):
        mock_llm.call_llm_for_rule_extraction.return_value = {
            "success": False,
            "error": "upstream",
            "error_type": "UpstreamError",
        }
        result = RuleParsingService.parse_document_version(document_version)
        assert result["success"] is False
        assert result["error"] == "upstream"

