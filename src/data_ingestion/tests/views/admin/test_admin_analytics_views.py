"""
API tests for admin analytics endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminAnalyticsViews:
    def test_statistics_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_statistics_success(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "data_sources" in resp.data["data"]
        assert "parsed_rules" in resp.data["data"]

    def test_cost_analytics_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/cost-analytics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "total_cost_usd" in resp.data["data"]
        assert "by_model" in resp.data["data"]

