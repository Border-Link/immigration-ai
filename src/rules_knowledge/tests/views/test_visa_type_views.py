"""
Tests for VisaType public API endpoints.
All tests use services, not direct model access.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge"


@pytest.mark.django_db
class TestVisaTypeViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-types/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_as_regular_user(self, client, regular_user, visa_type_uk):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-types/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_list_filter_by_jurisdiction(self, client, regular_user, visa_type_uk, visa_type_us):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-types/", {"jurisdiction": "UK"})
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(visa_type_uk.id) in ids
        assert str(visa_type_us.id) not in ids

    def test_create_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.post(
            f"{API_PREFIX}/visa-types/create/",
            {"jurisdiction": "UK", "code": "TEMP", "name": "Temp"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_success_as_staff(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-types/create/",
            {"jurisdiction": "UK", "code": " temp ", "name": "Temp", "is_active": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["code"] == "TEMP"

    def test_create_duplicate_returns_400(self, client, staff_user, visa_type_uk):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-types/create/",
            {"jurisdiction": visa_type_uk.jurisdiction, "code": visa_type_uk.code, "name": "Dup"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_not_found(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-types/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, client, regular_user, visa_type_uk):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-types/{visa_type_uk.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(visa_type_uk.id)

    def test_update_requires_staff(self, client, regular_user, visa_type_uk):
        client.force_authenticate(user=regular_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-types/{visa_type_uk.id}/update/",
            {"name": "X"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-types/{uuid4()}/update/",
            {"name": "X"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_success(self, client, staff_user, visa_type_uk):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-types/{visa_type_uk.id}/update/",
            {"name": "Skilled Worker Updated"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["name"] == "Skilled Worker Updated"

    def test_delete_requires_staff(self, client, regular_user, visa_type_uk):
        client.force_authenticate(user=regular_user)
        resp = client.delete(f"{API_PREFIX}/visa-types/{visa_type_uk.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.delete(f"{API_PREFIX}/visa-types/{uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_success(self, client, staff_user, visa_type_us):
        client.force_authenticate(user=staff_user)
        resp = client.delete(f"{API_PREFIX}/visa-types/{visa_type_us.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

