"""
Tests for admin VisaType endpoints.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge/admin"


@pytest.mark.django_db
class TestAdminVisaTypeViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_admin_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-types/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-types/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, client, admin_user, visa_type_uk):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-types/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail_not_found(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-types/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, client, admin_user, visa_type_uk):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-types/{visa_type_uk.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(visa_type_uk.id)

    def test_admin_activate_success(self, client, admin_user, visa_type_uk):
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-types/{visa_type_uk.id}/activate/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["is_active"] is False

    def test_admin_delete_success(self, client, admin_user, visa_type_us):
        client.force_authenticate(user=admin_user)
        resp = client.delete(f"{API_PREFIX}/visa-types/{visa_type_us.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_bulk_operation_mixed_results(self, client, admin_user, visa_type_service, visa_type_uk):
        extra = visa_type_service.create_visa_type(jurisdiction="UK", code="EXTRA", name="Extra")
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-types/bulk-operation/",
            {"visa_type_ids": [str(visa_type_uk.id), str(extra.id), str(uuid4())], "operation": "deactivate"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 2
        assert len(resp.data["data"]["failed"]) >= 1

