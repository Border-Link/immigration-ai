import pytest
from unittest.mock import patch

from data_ingestion.services.rule_parsing.streaming_handler import StreamingHandler


@pytest.mark.django_db
class TestStreamingHandler:
    @patch("data_ingestion.services.rule_parsing.streaming_handler.StreamingProcessor")
    def test_parse_document_version_streaming_merges_and_creates(self, mock_streaming, document_version):
        # Simulate chunk processing returning pre-extracted rules (bypasses LLM interaction).
        mock_streaming.process_in_chunks.return_value = [
            {"rules": [{"visa_code": "UK", "requirement_code": "FEE_PAYMENT", "description": "Applicant must pay the fee.", "condition_expression": {"==": [{"var": "fee_paid"}, True]}, "source_excerpt": "Fee"}], "tokens_used": 5, "estimated_cost": 0.001},
        ]
        mock_streaming.merge_chunk_results.return_value = {
            "rules": [{"visa_code": "UK", "requirement_code": "FEE_PAYMENT", "description": "Applicant must pay the fee.", "condition_expression": {"==": [{"var": "fee_paid"}, True]}, "source_excerpt": "Fee"}],
            "tokens_used": 5,
            "estimated_cost": 0.001,
            "model": "test",
        }

        result = StreamingHandler.parse_document_version_streaming(document_version, extracted_text="x" * 12000, jurisdiction="UK")
        assert result["success"] is True
        assert result["rules_created"] == 1
        assert result["validation_tasks_created"] == 1

