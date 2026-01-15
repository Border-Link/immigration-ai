"""
API tests for Rule Validation Task endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestRuleValidationTaskViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/validation-tasks/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/validation-tasks/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_list_filter_by_status(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/validation-tasks/?status=pending")
        assert resp.status_code == status.HTTP_200_OK
        assert all(item["status"] == "pending" for item in resp.data["data"])

    def test_pending_endpoint(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/validation-tasks/pending/")
        assert resp.status_code == status.HTTP_200_OK

    def test_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/validation-tasks/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/validation-tasks/{validation_task.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(validation_task.id)

    def test_update_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.patch(
            f"{API_PREFIX}/validation-tasks/{validation_task.id}/update/",
            {"status": "needs_revision", "reviewer_notes": "More evidence"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "needs_revision"

    def test_assign_success(self, api_client, staff_user, validation_task, reviewer_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/validation-tasks/{validation_task.id}/assign/",
            {"reviewer_id": str(reviewer_user.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert str(resp.data["data"]["assigned_to"]) == str(reviewer_user.id)

    def test_approve_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/validation-tasks/{validation_task.id}/approve/",
            {"reviewer_notes": "LGTM"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "approved"

    def test_reject_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/validation-tasks/{validation_task.id}/reject/",
            {"reviewer_notes": "Incorrect"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "rejected"

