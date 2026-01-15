"""
API tests for Source Document endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestSourceDocumentViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/source-documents/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, api_client, staff_user, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/source-documents/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_list_filter_by_data_source(self, api_client, staff_user, uk_data_source, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/source-documents/?data_source_id={uk_data_source.id}")
        assert resp.status_code == status.HTTP_200_OK
        # List serializer does not include data_source, so validate via non-empty result.
        assert len(resp.data["data"]) >= 1

    def test_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/source-documents/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, api_client, staff_user, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/source-documents/{source_document.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(source_document.id)

    def test_latest_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/source-documents/data-source/00000000-0000-0000-0000-000000000000/latest/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_latest_success(self, api_client, staff_user, uk_data_source, source_document):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/source-documents/data-source/{uk_data_source.id}/latest/")
        assert resp.status_code == status.HTTP_200_OK
        assert str(resp.data["data"]["data_source"]) == str(uk_data_source.id)

