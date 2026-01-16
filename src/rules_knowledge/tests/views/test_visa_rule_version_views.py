"""
Tests for VisaRuleVersion public API endpoints.
All tests use services, not direct model access.
"""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge"


@pytest.mark.django_db
class TestVisaRuleVersionViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_as_regular_user(self, client, regular_user, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_list_filter_by_visa_type_id(self, client, regular_user, visa_type_uk, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/", {"visa_type_id": str(visa_type_uk.id)})
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(rule_version_unpublished.id) in ids

    def test_create_requires_staff(self, client, regular_user, visa_type_uk):
        client.force_authenticate(user=regular_user)
        resp = client.post(
            f"{API_PREFIX}/visa-rule-versions/create/",
            {"visa_type_id": str(visa_type_uk.id), "effective_from": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_invalid_visa_type_returns_400(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-rule-versions/create/",
            {"visa_type_id": str(uuid4()), "effective_from": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_success_as_staff(self, client, staff_user, visa_type_uk):
        client.force_authenticate(user=staff_user)
        resp = client.post(
            f"{API_PREFIX}/visa-rule-versions/create/",
            {
                "visa_type_id": str(visa_type_uk.id),
                "effective_from": (timezone.now() + timedelta(days=10)).isoformat(),
                "effective_to": None,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["visa_type"] == str(visa_type_uk.id)

    def test_detail_not_found(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_success(self, client, regular_user, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(rule_version_unpublished.id)

    def test_update_requires_staff(self, client, regular_user, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/update/",
            {"effective_to": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-rule-versions/{uuid4()}/update/",
            {"effective_to": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_success_with_optimistic_locking(self, client, staff_user, rule_version_unpublished):
        client.force_authenticate(user=staff_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/update/",
            {"effective_to": (timezone.now() + timedelta(days=90)).isoformat(), "version": 1},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["version_number"] == 2

    def test_delete_requires_staff(self, client, regular_user, rule_version_unpublished):
        client.force_authenticate(user=regular_user)
        resp = client.delete(f"{API_PREFIX}/visa-rule-versions/{rule_version_unpublished.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self, client, staff_user):
        client.force_authenticate(user=staff_user)
        resp = client.delete(f"{API_PREFIX}/visa-rule-versions/{uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

