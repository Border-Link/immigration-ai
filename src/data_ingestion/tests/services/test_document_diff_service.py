"""
Tests for DocumentDiffService.
"""

import pytest


@pytest.mark.django_db
class TestDocumentDiffService:
    def test_get_all(self, document_diff_service, document_diff):
        qs = document_diff_service.get_all()
        assert qs.count() >= 1

    def test_get_by_change_type(self, document_diff_service, document_diff):
        qs = document_diff_service.get_by_change_type("fee_change")
        assert qs.count() >= 1
        assert all(d.change_type == "fee_change" for d in qs)

    def test_get_by_id_success(self, document_diff_service, document_diff):
        found = document_diff_service.get_by_id(str(document_diff.id))
        assert found is not None
        assert str(found.id) == str(document_diff.id)

    def test_get_by_id_not_found(self, document_diff_service):
        found = document_diff_service.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_get_by_versions_success(self, document_diff_service, document_version, second_document_version, document_diff):
        found = document_diff_service.get_by_versions(str(document_version.id), str(second_document_version.id))
        assert found is not None
        assert str(found.id) == str(document_diff.id)

    def test_get_by_versions_missing_returns_none(self, document_diff_service, document_version):
        found = document_diff_service.get_by_versions(str(document_version.id), "00000000-0000-0000-0000-000000000000")
        assert found is None

    def test_delete_document_diff_success(self, document_diff_service, document_diff):
        ok = document_diff_service.delete_document_diff(str(document_diff.id))
        assert ok is True
        assert document_diff_service.get_by_id(str(document_diff.id)) is None

    def test_delete_document_diff_not_found(self, document_diff_service):
        ok = document_diff_service.delete_document_diff("00000000-0000-0000-0000-000000000000")
        assert ok is False

    def test_get_by_filters(self, document_diff_service, document_diff):
        qs = document_diff_service.get_by_filters(change_type="fee_change")
        assert qs.count() >= 1

