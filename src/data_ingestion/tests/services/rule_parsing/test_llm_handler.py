from unittest.mock import patch

import pytest

from data_ingestion.services.rule_parsing.llm_handler import LLMHandler


class TestLLMHandler:
    @patch("data_ingestion.services.rule_parsing.llm_handler.ExternalLLMClient")
    @patch("data_ingestion.services.rule_parsing.llm_handler.track_usage")
    @patch("data_ingestion.services.rule_parsing.llm_handler.ResponseParser")
    def test_call_llm_for_rule_extraction_success(
        self, mock_parser, mock_track_usage, mock_client
    ):
        mock_client.return_value.extract_rules.return_value = {
            "model": "test",
            "usage": {"total_tokens": 12},
            "processing_time_ms": 5,
            "content": '{"visa_code":"UK","requirements":[]}',
        }
        mock_track_usage.return_value = {"estimated_cost": 0.01}
        mock_parser.parse_llm_response.return_value = {"visa_code": "UK", "requirements": []}
        mock_parser.extract_rules_from_response.return_value = []

        result = LLMHandler.call_llm_for_rule_extraction("text", jurisdiction="UK", document_version_id="dv")
        assert result["success"] is True
        assert result["model"] == "test"
        assert result["estimated_cost"] == 0.01

    @patch("data_ingestion.services.rule_parsing.llm_handler.ExternalLLMClient")
    def test_call_llm_for_rule_extraction_exception(self, mock_client):
        mock_client.return_value.extract_rules.side_effect = RuntimeError("boom")
        result = LLMHandler.call_llm_for_rule_extraction("text", jurisdiction="UK")
        assert result["success"] is False
        assert result["error_type"] == "RuntimeError"

