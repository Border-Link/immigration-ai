"""
Tests for DocumentVersionService.
"""

import pytest


@pytest.mark.django_db
class TestDocumentVersionService:
    def test_get_all(self, document_version_service, document_version):
        qs = document_version_service.get_all()
        assert qs.count() >= 1

    def test_get_by_source_document(self, document_version_service, source_document, document_version):
        qs = document_version_service.get_by_source_document(str(source_document.id))
        assert qs.count() >= 1
        assert all(v.source_document_id == source_document.id for v in qs)

    def test_get_by_source_document_invalid_returns_empty(self, document_version_service):
        qs = document_version_service.get_by_source_document("00000000-0000-0000-0000-000000000000")
        assert qs.count() == 0

    def test_get_by_id_success(self, document_version_service, document_version):
        found = document_version_service.get_by_id(str(document_version.id))
        assert found is not None
        assert str(found.id) == str(document_version.id)

    def test_get_by_id_not_found(self, document_version_service):
        found = document_version_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_get_latest_by_source_document(self, document_version_service, source_document, document_version):
        latest = document_version_service.get_latest_by_source_document(str(source_document.id))
        assert latest is not None
        assert latest.source_document_id == source_document.id

    def test_get_latest_by_source_document_not_found(self, document_version_service):
        latest = document_version_service.get_latest_by_source_document("00000000-0000-0000-0000-000000000000")
        assert latest is None

    def test_delete_document_version_success(self, document_version_service, document_version):
        ok = document_version_service.delete_document_version(str(document_version.id))
        assert ok is True
        assert document_version_service.get_by_id(str(document_version.id)) is None

    def test_delete_document_version_not_found(self, document_version_service):
        ok = document_version_service.delete_document_version("00000000-0000-0000-0000-000000000000")
        assert ok is False

    def test_get_by_filters(self, document_version_service, source_document, document_version):
        qs = document_version_service.get_by_filters(source_document_id=str(source_document.id))
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, document_version_service):
        stats = document_version_service.get_statistics()
        assert isinstance(stats, dict)

