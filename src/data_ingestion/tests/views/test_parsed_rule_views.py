"""
API tests for Parsed Rule endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestParsedRuleViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_list_filter_by_status(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/?status=pending")
        assert resp.status_code == status.HTTP_200_OK
        assert all(item["status"] == "pending" for item in resp.data["data"])

    def test_list_filter_by_visa_code(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/?visa_code=UK_SKILLED_WORKER")
        assert resp.status_code == status.HTTP_200_OK
        assert all(item["visa_code"] == "UK_SKILLED_WORKER" for item in resp.data["data"])

    def test_pending_endpoint(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/pending/")
        assert resp.status_code == status.HTTP_200_OK

    def test_detail_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/parsed-rules/{parsed_rule.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(parsed_rule.id)

    def test_update_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.patch(
            f"{API_PREFIX}/parsed-rules/{parsed_rule.id}/update/",
            {"description": "New description"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["description"] == "New description"

    def test_update_not_found(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.patch(
            f"{API_PREFIX}/parsed-rules/00000000-0000-0000-0000-000000000000/update/",
            {"description": "New description"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_status_update_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.patch(
            f"{API_PREFIX}/parsed-rules/{parsed_rule.id}/status/",
            {"status": "approved"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "approved"

