"""
Tests for admin DocumentType endpoints.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge/admin"


@pytest.mark.django_db
class TestAdminDocumentTypeViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_admin_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/document-types/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/document-types/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, client, admin_user, document_type):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/document-types/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail_not_found(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/document-types/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, client, admin_user, document_type):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/document-types/{document_type.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(document_type.id)

    def test_admin_activate_success(self, client, admin_user, document_type):
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/document-types/{document_type.id}/activate/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["is_active"] is False

    def test_admin_delete_success(self, client, admin_user, document_type):
        client.force_authenticate(user=admin_user)
        resp = client.delete(f"{API_PREFIX}/document-types/{document_type.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_bulk_operation_mixed_results(self, client, admin_user, document_type, document_type_service):
        extra = document_type_service.create_document_type(code="DOCB", name="Doc B")
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/document-types/bulk-operation/",
            {
                "document_type_ids": [str(document_type.id), str(extra.id), str(uuid4())],
                "operation": "deactivate",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "success" in resp.data["data"]
        assert "failed" in resp.data["data"]
        assert len(resp.data["data"]["success"]) >= 2
        assert len(resp.data["data"]["failed"]) >= 1

