"""
API tests for Data Source endpoints.
"""

import pytest
from rest_framework import status
from unittest.mock import patch, MagicMock


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestDataSourceViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/data-sources/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_as_staff(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/data-sources/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"] is not None

    def test_list_filter_by_jurisdiction(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/data-sources/?jurisdiction=UK")
        assert resp.status_code == status.HTTP_200_OK
        assert all(item["jurisdiction"] == "UK" for item in resp.data["data"])

    def test_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/data-sources/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/data-sources/{uk_data_source.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(uk_data_source.id)

    def test_create_requires_superadmin(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        payload = {"name": "X", "base_url": "https://x.example", "jurisdiction": "UK", "crawl_frequency": "daily"}
        resp = api_client.post(f"{API_PREFIX}/data-sources/create/", payload, format="json")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_create_success(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        payload = {"name": "X", "base_url": "https://x.example", "jurisdiction": "UK", "crawl_frequency": "daily"}
        resp = api_client.post(f"{API_PREFIX}/data-sources/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["name"] == "X"

    def test_update_not_found(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.patch(
            f"{API_PREFIX}/data-sources/00000000-0000-0000-0000-000000000000/update/",
            {"name": "Y"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_success(self, api_client, superadmin_user, uk_data_source):
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.patch(
            f"{API_PREFIX}/data-sources/{uk_data_source.id}/update/",
            {"name": "Updated"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["name"] == "Updated"

    @patch("data_ingestion.tasks.ingestion_tasks.ingest_data_source_task")
    def test_trigger_ingestion_async_success(self, mock_task, api_client, superadmin_user, uk_data_source):
        mock_task.delay.return_value = MagicMock(id="task-xyz")
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.post(
            f"{API_PREFIX}/data-sources/{uk_data_source.id}/ingest/",
            {"async_task": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["task_id"] == "task-xyz"

    def test_trigger_ingestion_not_found(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.post(
            f"{API_PREFIX}/data-sources/00000000-0000-0000-0000-000000000000/ingest/",
            {"async_task": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

