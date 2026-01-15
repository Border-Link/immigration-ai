import pytest
from unittest.mock import patch, MagicMock

from data_ingestion.tasks.ingestion_tasks import ingest_data_source_task


@pytest.mark.django_db
class TestIngestionTasks:
    @patch("data_ingestion.tasks.ingestion_tasks.IngestionService")
    def test_ingest_data_source_task_calls_service(self, mock_service):
        mock_service.ingest_data_source.return_value = {"success": True}
        result = ingest_data_source_task.run(data_source_id="123")  # call task body
        assert result["success"] is True
        mock_service.ingest_data_source.assert_called_once_with("123")

    @patch("data_ingestion.tasks.ingestion_tasks.IngestionService")
    @patch("data_ingestion.selectors.data_source_selector.DataSourceSelector")
    def test_ingest_all_active_sources_task_aggregates(self, mock_selector, mock_service):
        from data_ingestion.tasks.ingestion_tasks import ingest_all_active_sources_task

        ds1 = MagicMock(id="1", name="A")
        ds2 = MagicMock(id="2", name="B")
        qs = MagicMock()
        qs.__iter__.return_value = iter([ds1, ds2])
        qs.count.return_value = 2
        mock_selector.get_active.return_value = qs
        mock_service.ingest_data_source.side_effect = [{"success": True}, {"success": False}]

        res = ingest_all_active_sources_task.run()
        assert res["total_sources"] == 2
        assert res["processed"] == 2
        assert res["successful"] == 1
        assert res["failed"] == 1

    @patch("data_ingestion.tasks.ingestion_tasks.IngestionService")
    @patch("data_ingestion.selectors.data_source_selector.DataSourceSelector")
    def test_ingest_uk_sources_weekly_task_aggregates(self, mock_selector, mock_service):
        from data_ingestion.tasks.ingestion_tasks import ingest_uk_sources_weekly_task

        ds1 = MagicMock(id="1", name="UK1")
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.__iter__.return_value = iter([ds1])
        qs.count.return_value = 1
        mock_selector.get_by_jurisdiction.return_value = qs
        mock_service.ingest_data_source.return_value = {"success": True, "urls_processed": 2, "new_versions": 1, "rules_parsed": 3}

        res = ingest_uk_sources_weekly_task.run()
        assert res["jurisdiction"] == "UK"
        assert res["total_sources"] == 1
        assert res["processed"] == 1
        assert res["successful"] == 1
        assert res["urls_processed"] == 2


