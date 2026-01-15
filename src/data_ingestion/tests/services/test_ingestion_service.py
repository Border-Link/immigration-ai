"""
Tests for IngestionService (orchestration and utilities).
External systems are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock

from data_ingestion.services.ingestion_service import IngestionService


class TestIngestionServiceUtilities:
    def test_compute_diff_contains_unified_markers(self):
        diff = IngestionService._compute_diff("a\n", "b\n")
        assert "---old_version" in diff or "--- old_version" in diff
        assert "+b" in diff or "+b\n" in diff

    def test_classify_change_fee(self):
        diff = "+Fee is £200"
        assert IngestionService._classify_change(diff) == "fee_change"

    def test_classify_change_processing_time(self):
        diff = "+Processing time is 10 days"
        assert IngestionService._classify_change(diff) == "processing_time_change"

    def test_classify_change_requirement(self):
        diff = "+Minimum salary is £30000"
        assert IngestionService._classify_change(diff) == "requirement_change"

    def test_classify_change_major_update(self):
        assert IngestionService._classify_change("x" * 10001) == "major_update"

    def test_classify_change_minor_default(self):
        assert IngestionService._classify_change("+Some wording changed") == "minor_text"


@pytest.mark.django_db
class TestIngestionServiceOrchestration:
    @patch("data_ingestion.services.ingestion_service.DataSourceSelector")
    def test_ingest_data_source_not_found(self, mock_selector):
        mock_selector.get_by_id.side_effect = Exception("not found")
        res = IngestionService.ingest_data_source("missing")
        assert res["success"] is False

    @patch("data_ingestion.services.ingestion_service.DataSourceSelector")
    def test_ingest_data_source_inactive(self, mock_selector):
        ds = MagicMock(is_active=False, jurisdiction="UK")
        mock_selector.get_by_id.return_value = ds
        res = IngestionService.ingest_data_source("id")
        assert res["success"] is False
        assert "not active" in res["message"].lower()

    @patch("data_ingestion.services.ingestion_service.DataSourceRepository")
    @patch("data_ingestion.services.ingestion_service.IngestionSystemFactory")
    @patch("data_ingestion.services.ingestion_service.DataSourceSelector")
    def test_ingest_data_source_unsupported_jurisdiction(self, mock_selector, mock_factory, mock_repo):
        ds = MagicMock(is_active=True, jurisdiction="XX")
        mock_selector.get_by_id.return_value = ds
        mock_factory.create.return_value = None
        res = IngestionService.ingest_data_source("id")
        assert res["success"] is False
        assert "unsupported jurisdiction" in res["message"].lower()
        mock_repo.update_last_fetched.assert_not_called()

    @patch("data_ingestion.services.ingestion_service.DataSourceRepository")
    @patch("data_ingestion.services.ingestion_service.IngestionService._process_url")
    @patch("data_ingestion.services.ingestion_service.IngestionSystemFactory")
    @patch("data_ingestion.services.ingestion_service.DataSourceSelector")
    def test_ingest_data_source_processes_urls_and_aggregates(
        self, mock_selector, mock_factory, mock_process_url, mock_repo
    ):
        ds = MagicMock(is_active=True, jurisdiction="UK")
        mock_selector.get_by_id.return_value = ds
        ingestion_system = MagicMock()
        ingestion_system.get_document_urls.return_value = ["u1", "u2"]
        mock_factory.create.return_value = ingestion_system

        mock_process_url.side_effect = [
            {"new_version": True, "diff_created": True, "rules_parsed": 2, "validation_tasks_created": 2},
            {"new_version": False, "diff_created": False, "rules_parsed": 0, "validation_tasks_created": 0},
        ]

        res = IngestionService.ingest_data_source("id")
        assert res["success"] is True
        assert res["urls_processed"] == 2
        assert res["new_versions"] == 1
        assert res["diffs_created"] == 1
        assert res["rules_parsed"] == 2
        assert res["validation_tasks_created"] == 2
        mock_repo.update_last_fetched.assert_called_once()

