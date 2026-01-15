"""
Admin API tests for case status history endpoints.
"""

import pytest
from rest_framework import status
import uuid


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestAdminCaseStatusHistoryEndpoints:
    def test_admin_status_history_requires_staff(self, api_client, case_owner, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/admin/cases/{case.id}/status-history/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_status_history_list_and_detail(self, api_client, admin_user, case_service, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        current = case_service.get_by_id(str(case.id))
        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            status="evaluated",
            reason="evaluate",
        )
        assert updated is not None
        assert error is None
        assert http_status is None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/cases/{case.id}/status-history/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["items"]
        history_id = resp.data["data"]["items"][0]["id"]

        resp2 = api_client.get(f"{BASE}/admin/status-history/{history_id}/")
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data["data"]["id"] == history_id

    def test_admin_status_history_detail_not_found_returns_404(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/status-history/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

