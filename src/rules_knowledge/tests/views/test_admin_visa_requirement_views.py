"""
Tests for admin VisaRequirement endpoints.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge/admin"


@pytest.mark.django_db
class TestAdminVisaRequirementViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_admin_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-requirements/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, client, admin_user, visa_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail_not_found(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, client, admin_user, visa_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/{visa_requirement.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(visa_requirement.id)

    def test_admin_update_success(self, client, admin_user, visa_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-requirements/{visa_requirement.id}/update/",
            {"is_mandatory": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        # Response uses API contract is_active mapped to is_mandatory
        assert resp.data["data"]["is_active"] is False

    def test_admin_bulk_operation_mixed_results(self, client, admin_user, visa_requirement, visa_requirement_service):
        extra = visa_requirement_service.create_requirement(
            rule_version_id=str(visa_requirement.rule_version_id),
            requirement_code="EXTRA",
            rule_type="eligibility",
            description="Extra",
            condition_expression={"==": [1, 1]},
            is_mandatory=True,
        )
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-requirements/bulk-operation/",
            {"requirement_ids": [str(visa_requirement.id), str(extra.id), str(uuid4())], "operation": "set_optional"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 2
        assert len(resp.data["data"]["failed"]) >= 1

