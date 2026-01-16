"""
Tests for admin VisaRuleVersion endpoints (list/detail/update/publish/delete/bulk).
"""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge/admin"


@pytest.mark.django_db
class TestAdminVisaRuleVersionViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_admin_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, client, admin_user, rule_version_unpublished):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail_not_found(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, client, admin_user, rule_version_unpublished):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(rule_version_unpublished.id)

    def test_admin_update_success_with_optimistic_locking(self, client, admin_user, rule_version_unpublished):
        client.force_authenticate(user=admin_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/update/",
            {"effective_to": (timezone.now() + timedelta(days=10)).isoformat(), "version": 1},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["version_number"] == 2

    def test_admin_publish_version_conflict_returns_400(self, client, admin_user, rule_version_unpublished):
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/publish/",
            {"is_published": True, "version": 999},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_publish_success(self, client, admin_user, rule_version_unpublished):
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/publish/",
            {"is_published": True, "version": 1},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["version_number"] == 2

    def test_admin_bulk_publish_mixed_results(self, client, admin_user, visa_rule_version_service, visa_type_uk):
        rv2 = visa_rule_version_service.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() + timedelta(days=20),
        )
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-rule-versions/bulk-operation/",
            {"rule_version_ids": [str(rv2.id), str(uuid4())], "operation": "publish"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 1
        assert len(resp.data["data"]["failed"]) >= 1

