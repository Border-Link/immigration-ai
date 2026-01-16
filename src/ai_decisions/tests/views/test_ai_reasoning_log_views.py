import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/ai-decisions"


@pytest.mark.django_db
class TestAIReasoningLogViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/ai-reasoning-logs/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_regular_user_forbidden(self, api_client, case_owner, reasoning_log):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/ai-reasoning-logs/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_reviewer_allowed(self, api_client, reviewer_user, reasoning_log):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-reasoning-logs/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_list_filter_by_case_id(self, api_client, reviewer_user, reasoning_log):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-reasoning-logs/?case_id={reasoning_log.case_id}")
        assert resp.status_code == status.HTTP_200_OK

    def test_detail_reviewer_allowed(self, api_client, reviewer_user, reasoning_log):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-reasoning-logs/{reasoning_log.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(reasoning_log.id)

    def test_detail_not_found(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-reasoning-logs/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

