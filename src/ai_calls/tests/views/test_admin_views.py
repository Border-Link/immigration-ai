"""
API tests for admin endpoints in `ai_calls`.
"""

import pytest
from rest_framework import status


BASE = "/api/v1/ai-calls"


@pytest.mark.django_db
class TestAdminCallSessionListAndDetail:
    def test_admin_list_requires_auth(self, api_client):
        resp = api_client.get(f"{BASE}/admin/sessions/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/admin/sessions/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, api_client, admin_user, call_session_created):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/sessions/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_list_filters(self, api_client, admin_user, call_session_created):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/sessions/", {"status": "created"})
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_detail_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/sessions/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, api_client, admin_user, call_session_created):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/sessions/{call_session_created.id}/")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAdminAnalytics:
    def test_statistics_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/admin/statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_statistics_success(self, api_client, admin_user, call_session_created):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "total_sessions" in resp.data["data"]

    def test_guardrail_analytics_success(self, api_client, admin_user, call_session_created):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/guardrail-analytics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "total_guardrail_events" in resp.data["data"]

