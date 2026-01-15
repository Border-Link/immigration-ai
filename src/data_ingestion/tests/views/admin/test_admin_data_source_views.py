"""
API tests for admin data source endpoints.
"""

import pytest
from rest_framework import status
from unittest.mock import patch, MagicMock


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminDataSourceViews:
    def test_admin_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/admin/data-sources/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, api_client, reviewer_user):
        # reviewer_user is staff=True per fixture, so use a non-staff user
        from users_access.services.user_service import UserService
        import uuid
        user = UserService.create_user(email=f"basic-{uuid.uuid4().hex[:8]}@example.com", password="pass123")
        UserService.activate_user(user)
        api_client.force_authenticate(user=user)
        resp = api_client.get(f"{API_PREFIX}/admin/data-sources/")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_admin_list_success(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/data-sources/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_admin_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/data-sources/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/data-sources/{uk_data_source.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(uk_data_source.id)

    def test_admin_activate_success(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/data-sources/{uk_data_source.id}/activate/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        # BaseAdminActivateAPI returns data=None on success; verify via refetch.
        from data_ingestion.services.data_source_service import DataSourceService
        updated = DataSourceService.get_by_id(str(uk_data_source.id))
        assert updated is not None
        assert updated.is_active is False

    def test_admin_delete_success(self, api_client, staff_user, uk_data_source):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/data-sources/{uk_data_source.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    @patch("data_ingestion.tasks.ingestion_tasks.ingest_data_source_task")
    def test_admin_bulk_operation_trigger_ingestion(self, mock_task, api_client, staff_user, uk_data_source):
        mock_task.delay.return_value = MagicMock(id="task-1")
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/data-sources/bulk-operation/",
            {"operation": "trigger_ingestion", "data_source_ids": [str(uk_data_source.id)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

