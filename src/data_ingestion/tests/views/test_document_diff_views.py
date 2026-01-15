"""
API tests for Document Diff endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestDocumentDiffViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/document-diffs/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-diffs/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_list_filter_by_change_type(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-diffs/?change_type=fee_change")
        assert resp.status_code == status.HTTP_200_OK
        assert all(item["change_type"] == "fee_change" for item in resp.data["data"])

    def test_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-diffs/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, api_client, staff_user, document_diff):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-diffs/{document_diff.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(document_diff.id)

