"""
Tests for DocumentType public API endpoints.
All tests use services, not direct model access.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge"


@pytest.mark.django_db
class TestDocumentTypeViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/document-types/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_as_regular_user(self, client, regular_user, document_type):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/document-types/")
        assert resp.status_code == status.HTTP_200_OK
        assert "data" in resp.data
        assert "items" in resp.data["data"]

    def test_list_filter_is_active_true(self, client, regular_user, document_type, inactive_document_type):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/document-types/", {"is_active": "true"})
        assert resp.status_code == status.HTTP_200_OK
        items = resp.data["data"]["items"]
        ids = {item["id"] for item in items}
        assert str(document_type.id) in ids
        assert str(inactive_document_type.id) not in ids

    def test_create_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.post(
            f"{API_PREFIX}/document-types/create/",
            {"code": "DOCX", "name": "Doc X"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_success_as_staff(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/document-types/create/",
            {"code": " docx ", "name": "Doc X", "description": "", "is_active": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["code"] == "DOCX"  # serializer normalizes

    def test_create_duplicate_returns_400(self, client, staff_user, document_type):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/document-types/create/",
            {"code": document_type.code, "name": "Dup"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_not_found(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/document-types/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, client, regular_user, document_type):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/document-types/{document_type.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(document_type.id)

    def test_update_requires_staff(self, client, regular_user, document_type):
        client.force_authenticate(user=regular_user)
        resp = client.patch(
            f"{API_PREFIX}/document-types/{document_type.id}/update/",
            {"name": "X"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/document-types/{uuid4()}/update/",
            {"name": "X"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_success(self, client, staff_user, document_type):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/document-types/{document_type.id}/update/",
            {"name": "Passport Updated"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["name"] == "Passport Updated"

    def test_delete_requires_staff(self, client, regular_user, document_type):
        client.force_authenticate(user=regular_user)
        resp = client.delete(f"{API_PREFIX}/document-types/{document_type.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.delete(f"{API_PREFIX}/document-types/{uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_success(self, client, staff_user, document_type):
        client.force_authenticate(user=staff_user)
        resp = client.delete(f"{API_PREFIX}/document-types/{document_type.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

