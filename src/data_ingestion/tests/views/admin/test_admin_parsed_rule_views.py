"""
API tests for admin parsed rule endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminParsedRuleViews:
    def test_list_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/parsed-rules/?status=pending&visa_code=UK_SKILLED_WORKER")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_detail_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/parsed-rules/{parsed_rule.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(parsed_rule.id)

    def test_update_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.patch(
            f"{API_PREFIX}/admin/parsed-rules/{parsed_rule.id}/update/",
            {"status": "approved", "confidence_score": 0.95},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "approved"

    def test_bulk_approve_success(self, api_client, staff_user, parsed_rule):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/parsed-rules/bulk-operation/",
            {"operation": "approve", "rule_ids": [str(parsed_rule.id)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

