import pytest
from rest_framework import status


API_PREFIX = "/api/v1/ai-decisions"


@pytest.mark.django_db
class TestAdminAIReasoningLogViews:
    def test_admin_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/admin/ai-reasoning-logs/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_forbidden_for_non_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/ai-reasoning-logs/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_allowed(self, api_client, admin_user, reasoning_log):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/ai-reasoning-logs/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail(self, api_client, admin_user, reasoning_log):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/ai-reasoning-logs/{reasoning_log.id}/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_bulk_delete(self, api_client, admin_user, reasoning_log, ai_reasoning_log_service):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/ai-reasoning-logs/bulk-operation/",
            {"log_ids": [str(reasoning_log.id)], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert ai_reasoning_log_service.get_by_id(str(reasoning_log.id)) is None

    def test_admin_bulk_invalid_operation_is_reported_not_500(self, api_client, admin_user, reasoning_log):
        """
        BaseBulkOperationAPI reports per-entity failures and still returns 200.
        The key requirement is that we don't 500 on invalid operation.
        """
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/ai-reasoning-logs/bulk-operation/",
            {"log_ids": [str(reasoning_log.id)], "operation": "not-a-real-op"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "failed" in resp.data["data"]
        assert len(resp.data["data"]["failed"]) == 1

    def test_admin_delete_endpoint_success(self, api_client, admin_user, reasoning_log, ai_reasoning_log_service):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/ai-reasoning-logs/{reasoning_log.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK
        assert ai_reasoning_log_service.get_by_id(str(reasoning_log.id)) is None

    def test_admin_delete_endpoint_not_found(self, api_client, admin_user):
        import uuid

        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/ai-reasoning-logs/{uuid.uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
