import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/ai-decisions"


@pytest.mark.django_db
class TestAICitationViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/ai-citations/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_regular_user_forbidden(self, api_client, case_owner, citation):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/ai-citations/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_reviewer_allowed(self, api_client, reviewer_user, citation):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-citations/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_list_filter_by_reasoning_log_id(self, api_client, reviewer_user, citation):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-citations/?reasoning_log_id={citation.reasoning_log_id}")
        assert resp.status_code == status.HTTP_200_OK

    def test_detail_reviewer_allowed(self, api_client, reviewer_user, citation):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-citations/{citation.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(citation.id)

    def test_detail_not_found(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/ai-citations/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

