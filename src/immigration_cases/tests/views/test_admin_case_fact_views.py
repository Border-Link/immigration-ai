"""
Admin API tests for case fact management endpoints.
"""

import pytest
from rest_framework import status
import uuid


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestAdminCaseFactEndpoints:
    def test_admin_case_fact_list_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/admin/case-facts/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_case_fact_list_success(self, api_client, admin_user, paid_case_with_fact):
        _case, fact = paid_case_with_fact
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/case-facts/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(fact.id) in ids

    def test_admin_case_fact_detail_success(self, api_client, admin_user, paid_case_with_fact):
        _case, fact = paid_case_with_fact
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/case-facts/{fact.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(fact.id)

    def test_admin_case_fact_update_success(self, api_client, admin_user, paid_case_with_fact):
        _case, fact = paid_case_with_fact
        api_client.force_authenticate(user=admin_user)
        resp = api_client.patch(
            f"{BASE}/admin/case-facts/{fact.id}/update/",
            {"source": "reviewer"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["source"] == "reviewer"

    def test_admin_case_fact_bulk_update_source_requires_source(self, api_client, admin_user, paid_case_with_fact):
        _case, fact = paid_case_with_fact
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{BASE}/admin/case-facts/bulk-operation/",
            {"case_fact_ids": [str(fact.id)], "operation": "update_source"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["failed"]) == 1

    def test_admin_case_fact_delete_success(self, api_client, admin_user, paid_case_with_fact):
        _case, fact = paid_case_with_fact
        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{BASE}/admin/case-facts/{fact.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

        # Deleted -> detail should return 404
        resp2 = api_client.get(f"{BASE}/admin/case-facts/{fact.id}/")
        assert resp2.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_case_fact_bulk_delete_mixed_results(self, api_client, admin_user, case_fact_service, paid_case_with_fact):
        case, fact1 = paid_case_with_fact
        fact2 = case_fact_service.create_case_fact(str(case.id), "salary", 1000, "user")
        assert fact2 is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{BASE}/admin/case-facts/bulk-operation/",
            {"case_fact_ids": [str(fact1.id), str(fact2.id), str(uuid.uuid4())], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) == 2
        assert len(resp.data["data"]["failed"]) == 1

