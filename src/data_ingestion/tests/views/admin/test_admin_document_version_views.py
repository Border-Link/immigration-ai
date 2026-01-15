"""
API tests for admin document version endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminDocumentVersionViews:
    def test_list_success(self, api_client, staff_user, document_version, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/document-versions/?source_document_id={source_document.id}")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_detail_success(self, api_client, staff_user, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/document-versions/{document_version.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(document_version.id)

    def test_delete_success(self, api_client, staff_user, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/document-versions/{document_version.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_bulk_delete_success(self, api_client, staff_user, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/document-versions/bulk-operation/",
            {"operation": "delete", "version_ids": [str(document_version.id)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

