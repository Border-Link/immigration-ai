"""
Admin API tests for immigration cases analytics/statistics.
"""

import pytest
from rest_framework import status


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestAdminStatistics:
    def test_statistics_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/admin/statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_statistics_success_shape(self, api_client, admin_user, paid_case_with_fact):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        assert "cases" in data
        assert "case_facts" in data
        assert "total_cases" in data["cases"]
        assert "total_facts" in data["case_facts"]

    def test_statistics_invalid_date_range_returns_400(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(
            f"{BASE}/admin/statistics/?date_from=2026-01-15T10:00:00Z&date_to=2026-01-14T10:00:00Z"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

