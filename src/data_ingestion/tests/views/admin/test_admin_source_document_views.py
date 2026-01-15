"""
API tests for admin source document endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminSourceDocumentViews:
    def test_list_success(self, api_client, staff_user, source_document, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/source-documents/?data_source_id={uk_data_source.id}&http_status=200&has_error=false")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_detail_success(self, api_client, staff_user, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/source-documents/{source_document.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(source_document.id)

    def test_delete_success(self, api_client, staff_user, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/source-documents/{source_document.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_bulk_delete_success(self, api_client, staff_user, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/source-documents/bulk-operation/",
            {"operation": "delete", "document_ids": [str(source_document.id)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

