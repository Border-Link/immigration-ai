"""
API tests for admin rule validation task endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminRuleValidationTaskViews:
    def test_list_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/validation-tasks/?status=pending")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_detail_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/validation-tasks/{validation_task.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(validation_task.id)

    def test_update_assign_success(self, api_client, staff_user, validation_task, reviewer_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.patch(
            f"{API_PREFIX}/admin/validation-tasks/{validation_task.id}/update/",
            {"assigned_to": str(reviewer_user.id), "reviewer_notes": "Assigned"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert str(resp.data["data"]["assigned_to"]) == str(reviewer_user.id)

    def test_bulk_approve_success(self, api_client, staff_user, validation_task):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/validation-tasks/bulk-operation/",
            {"operation": "approve", "task_ids": [str(validation_task.id)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

