"""
API tests for admin document diff endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminDocumentDiffViews:
    def test_list_success(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/document-diffs/?change_type=fee_change")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_detail_success(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/document-diffs/{document_diff.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(document_diff.id)

    def test_delete_success(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/document-diffs/{document_diff.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_bulk_delete_success(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/document-diffs/bulk-operation/",
            {"operation": "delete", "diff_ids": [str(document_diff.id)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

