import pytest
from rest_framework import status


API_PREFIX = "/api/v1/ai-decisions"


@pytest.mark.django_db
class TestAdminAIDecisionsAnalyticsViews:
    def test_statistics_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_statistics_forbidden_for_non_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_statistics_allowed(self, api_client, admin_user, eligibility_result, reasoning_log, citation):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        assert set(resp.data["data"].keys()) == {"eligibility_results", "ai_reasoning_logs", "ai_citations"}

    def test_token_usage_validation(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        # date_to < date_from should 400
        resp = api_client.get(
            f"{API_PREFIX}/admin/token-usage/?date_from=2026-01-02T00:00:00Z&date_to=2026-01-01T00:00:00Z"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_usage_success(self, api_client, admin_user, reasoning_log):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/token-usage/")
        assert resp.status_code == status.HTTP_200_OK
        assert "total_tokens" in resp.data["data"]

    def test_citation_quality_validation(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(
            f"{API_PREFIX}/admin/citation-quality/?date_from=2026-01-02T00:00:00Z&date_to=2026-01-01T00:00:00Z"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_citation_quality_success(self, api_client, admin_user, citation):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/citation-quality/")
        assert resp.status_code == status.HTTP_200_OK
        assert "quality_distribution" in resp.data["data"]

