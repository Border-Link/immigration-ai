"""
Tests for VisaRequirement public API endpoints.
All tests use services, not direct model access.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge"


@pytest.mark.django_db
class TestVisaRequirementViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-requirements/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_as_regular_user(self, client, regular_user, visa_requirement):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_list_filter_by_rule_version_id(self, client, regular_user, visa_requirement, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/", {"rule_version_id": str(rule_version_unpublished.id)})
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(visa_requirement.id) in ids

    def test_create_requires_staff(self, client, regular_user, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.post(
            f"{API_PREFIX}/visa-requirements/create/",
            {
                "rule_version_id": str(rule_version_unpublished.id),
                "requirement_code": "R1",
                "description": "Desc",
                "condition_expression": {"==": [1, 1]},
                "is_active": True,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_invalid_rule_version_returns_400(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-requirements/create/",
            {
                "rule_version_id": str(uuid4()),
                "requirement_code": "R1",
                "description": "Desc",
                "condition_expression": {"==": [1, 1]},
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_invalid_json_logic_returns_400(self, client, staff_user, rule_version_unpublished):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-requirements/create/",
            {
                "rule_version_id": str(rule_version_unpublished.id),
                "requirement_code": "BAD",
                "description": "Bad",
                "condition_expression": {"bad_operator": [1, 2]},
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_success_as_staff(self, client, staff_user, rule_version_unpublished):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-requirements/create/",
            {
                "rule_version_id": str(rule_version_unpublished.id),
                "requirement_code": "MIN_SALARY",
                "description": "Salary >= 30000",
                "condition_expression": {">=": [{"var": "salary"}, 30000]},
                "is_active": False,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["requirement_code"] == "MIN_SALARY"
        assert resp.data["data"]["is_active"] is False

    def test_detail_not_found(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, client, regular_user, visa_requirement):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-requirements/{visa_requirement.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(visa_requirement.id)

    def test_update_requires_staff(self, client, regular_user, visa_requirement):
        client.force_authenticate(user=regular_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-requirements/{visa_requirement.id}/update/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-requirements/{uuid4()}/update/",
            {"description": "X"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_success_maps_is_active(self, client, staff_user, visa_requirement):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-requirements/{visa_requirement.id}/update/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["is_active"] is False

    def test_delete_requires_staff(self, client, regular_user, visa_requirement):
        client.force_authenticate(user=regular_user)
        resp = client.delete(f"{API_PREFIX}/visa-requirements/{visa_requirement.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.delete(f"{API_PREFIX}/visa-requirements/{uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

