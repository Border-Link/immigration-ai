"""
Tests for SourceDocumentService.
"""

import pytest


@pytest.mark.django_db
class TestSourceDocumentService:
    def test_get_all(self, source_document_service, source_document):
        qs = source_document_service.get_all()
        assert qs.count() >= 1

    def test_get_by_data_source(self, source_document_service, uk_data_source, source_document):
        qs = source_document_service.get_by_data_source(str(uk_data_source.id))
        assert qs.count() >= 1
        assert all(d.data_source_id == uk_data_source.id for d in qs)

    def test_get_by_data_source_invalid_returns_empty(self, source_document_service):
        qs = source_document_service.get_by_data_source("00000000-0000-0000-0000-000000000000")
        assert qs.count() == 0

    def test_get_by_id_success(self, source_document_service, source_document):
        found = source_document_service.get_by_id(str(source_document.id))
        assert found is not None
        assert str(found.id) == str(source_document.id)

    def test_get_by_id_not_found(self, source_document_service):
        found = source_document_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_get_latest_by_data_source(self, source_document_service, uk_data_source, source_document):
        latest = source_document_service.get_latest_by_data_source(str(uk_data_source.id))
        assert latest is not None
        assert latest.data_source_id == uk_data_source.id

    def test_get_latest_by_data_source_not_found(self, source_document_service):
        latest = source_document_service.get_latest_by_data_source("00000000-0000-0000-0000-000000000000")
        assert latest is None

    def test_delete_source_document_success(self, source_document_service, source_document):
        ok = source_document_service.delete_source_document(str(source_document.id))
        assert ok is True
        assert source_document_service.get_by_id(str(source_document.id)) is None

    def test_delete_source_document_not_found(self, source_document_service):
        ok = source_document_service.delete_source_document("00000000-0000-0000-0000-000000000000")
        assert ok is False

    def test_get_by_filters(self, source_document_service, uk_data_source, source_document):
        qs = source_document_service.get_by_filters(
            data_source_id=str(uk_data_source.id),
            has_error=False,
            http_status=200,
        )
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, source_document_service):
        stats = source_document_service.get_statistics()
        assert isinstance(stats, dict)

