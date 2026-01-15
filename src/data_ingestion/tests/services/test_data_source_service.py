"""
Tests for DataSourceService.
All tests exercise service APIs (no direct model calls).
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestDataSourceService:
    def test_create_data_source_success(self, data_source_service):
        ds = data_source_service.create_data_source(
            name="Test Source",
            base_url="https://example.com/base",
            jurisdiction="UK",
            crawl_frequency="daily",
            is_active=True,
        )
        assert ds is not None
        assert ds.name == "Test Source"
        assert ds.jurisdiction == "UK"
        assert ds.is_active is True

    def test_get_by_id_not_found(self, data_source_service):
        ds = data_source_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert ds is None

    def test_get_all_and_get_active(self, data_source_service):
        data_source_service.create_data_source("A", "https://a.example", "UK", is_active=True)
        data_source_service.create_data_source("B", "https://b.example", "UK", is_active=False)
        all_sources = data_source_service.get_all()
        active_sources = data_source_service.get_active()
        assert all_sources.count() >= 2
        assert active_sources.filter(is_active=True).count() >= 1

    def test_get_by_jurisdiction(self, data_source_service):
        data_source_service.create_data_source("UK1", "https://uk.example/1", "UK", is_active=True)
        data_source_service.create_data_source("UK2", "https://uk.example/2", "UK", is_active=True)
        sources = data_source_service.get_by_jurisdiction("UK")
        assert sources.count() >= 2
        assert all(s.jurisdiction == "UK" for s in sources)

    def test_update_data_source(self, data_source_service, uk_data_source):
        updated = data_source_service.update_data_source(uk_data_source, name="Updated Name")
        assert updated is not None
        assert updated.name == "Updated Name"

    def test_activate_data_source(self, data_source_service, uk_data_source):
        updated = data_source_service.activate_data_source(uk_data_source, False)
        assert updated is not None
        assert updated.is_active is False

    def test_delete_data_source_success(self, data_source_service, uk_data_source):
        ok = data_source_service.delete_data_source(str(uk_data_source.id))
        assert ok is True
        assert data_source_service.get_by_id(str(uk_data_source.id)) is None

    def test_delete_data_source_not_found(self, data_source_service):
        ok = data_source_service.delete_data_source("00000000-0000-0000-0000-000000000000")
        assert ok is False

    @patch("data_ingestion.tasks.ingestion_tasks.ingest_data_source_task")
    def test_trigger_ingestion_async(self, mock_task, data_source_service, uk_data_source):
        mock_task.delay.return_value = MagicMock(id="task-123")
        result = data_source_service.trigger_ingestion(str(uk_data_source.id), async_task=True)
        assert result["status"] == "queued"
        assert result["task_id"] == "task-123"
        mock_task.delay.assert_called_once()

    @patch("data_ingestion.services.ingestion_service.IngestionService.ingest_data_source")
    def test_trigger_ingestion_sync(self, mock_ingest, data_source_service, uk_data_source):
        mock_ingest.return_value = {"success": True, "urls_processed": 1}
        result = data_source_service.trigger_ingestion(str(uk_data_source.id), async_task=False)
        assert result["success"] is True
        mock_ingest.assert_called_once_with(str(uk_data_source.id))

    def test_get_statistics_returns_dict(self, data_source_service):
        stats = data_source_service.get_statistics()
        assert isinstance(stats, dict)

