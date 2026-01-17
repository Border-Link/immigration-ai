import pytest


@pytest.mark.django_db
class TestDataIngestionOptimisticLocking:
    def test_data_source_update_version_conflict_returns_none(self, data_source_service, uk_data_source):
        updated = data_source_service.update_data_source(uk_data_source, version=999, name="new name")
        assert updated is None

    def test_parsed_rule_update_version_conflict_returns_none(self, parsed_rule_service, parsed_rule):
        updated = parsed_rule_service.update_parsed_rule(str(parsed_rule.id), version=999, description="changed")
        assert updated is None

    def test_validation_task_update_version_conflict_returns_none(self, rule_validation_task_service, validation_task):
        updated = rule_validation_task_service.update_task(str(validation_task.id), version=999, status="approved")
        assert updated is None

    def test_soft_delete_filters_deleted_data_source(self, data_source_service, uk_data_source):
        from data_ingestion.selectors.data_source_selector import DataSourceSelector

        assert data_source_service.get_by_id(str(uk_data_source.id)) is not None

        ok = data_source_service.delete_data_source(str(uk_data_source.id))
        assert ok is True

        assert data_source_service.get_by_id(str(uk_data_source.id)) is None
        assert DataSourceSelector.get_by_id(str(uk_data_source.id)) is None

