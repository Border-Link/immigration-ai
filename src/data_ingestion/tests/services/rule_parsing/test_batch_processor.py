import pytest
from unittest.mock import patch

from data_ingestion.services.rule_parsing.batch_processor import BatchProcessor


@pytest.mark.django_db
class TestBatchProcessor:
    @patch("data_ingestion.services.rule_parsing.service.RuleParsingService.parse_document_version")
    def test_parse_document_versions_batch_sequential(self, mock_parse, document_version):
        mock_parse.return_value = {"success": True, "rules_created": 0, "message": "Already parsed"}
        result = BatchProcessor.parse_document_versions_batch([document_version], use_parallel=False)
        assert result["total"] == 1
        assert result["failed"] == 0
        assert len(result["results"]) == 1

