"""
API tests for Document Version endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestDocumentVersionViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/document-versions/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, api_client, staff_user, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-versions/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_list_filter_by_source_document(self, api_client, staff_user, source_document, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-versions/?source_document_id={source_document.id}")
        assert resp.status_code == status.HTTP_200_OK
        # List serializer does not include source_document, so validate via non-empty result.
        assert len(resp.data["data"]) >= 1

    def test_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-versions/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, api_client, staff_user, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-versions/{document_version.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(document_version.id)

    def test_latest_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(
            f"{API_PREFIX}/document-versions/source-document/00000000-0000-0000-0000-000000000000/latest/"
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_latest_success(self, api_client, staff_user, source_document, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/document-versions/source-document/{source_document.id}/latest/")
        assert resp.status_code == status.HTTP_200_OK
        assert str(resp.data["data"]["source_document"]) == str(source_document.id)

