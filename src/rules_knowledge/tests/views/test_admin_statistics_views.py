"""
Tests for admin statistics endpoint.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge/admin"


@pytest.mark.django_db
class TestRulesKnowledgeStatisticsAPI:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/statistics/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, client, admin_user, document_type, visa_type_uk, rule_version_published_current, visa_requirement, visa_document_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        assert "document_types" in data
        assert "visa_types" in data
        assert "visa_rule_versions" in data
        assert data["document_types"]["total"] >= 1

