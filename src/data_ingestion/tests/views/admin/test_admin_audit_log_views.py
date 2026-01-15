"""
API tests for admin audit log endpoints.
"""

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminAuditLogViews:
    def test_list_success(self, api_client, staff_user, audit_log):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/audit-logs/?action=parse_started&status=success")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) >= 1

    def test_detail_success(self, api_client, staff_user, audit_log):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{API_PREFIX}/admin/audit-logs/{audit_log.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(audit_log.id)

