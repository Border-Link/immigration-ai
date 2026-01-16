"""
Tests for admin VisaDocumentRequirement endpoints.
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/rules-knowledge/admin"


@pytest.mark.django_db
class TestAdminVisaDocumentRequirementViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_admin_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/visa-document-requirements/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_requires_staff(self, client, regular_user):
        client.force_authenticate(user=regular_user)
        resp = client.get(f"{API_PREFIX}/visa-document-requirements/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, client, admin_user, visa_document_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-document-requirements/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail_not_found(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-document-requirements/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_success(self, client, admin_user, visa_document_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/visa-document-requirements/{visa_document_requirement.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(visa_document_requirement.id)

    def test_admin_update_success(self, client, admin_user, visa_document_requirement):
        client.force_authenticate(user=admin_user)
        resp = client.patch(
            f"{API_PREFIX}/visa-document-requirements/{visa_document_requirement.id}/update/",
            {"mandatory": False, "conditional_logic": {"description": "optional"}},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["mandatory"] is False

    def test_admin_bulk_operation_mixed_results(self, client, admin_user, visa_document_requirement, visa_document_requirement_service, rule_version_unpublished, document_type_service):
        doc2 = document_type_service.create_document_type(code="DOCZ", name="Doc Z")
        extra = visa_document_requirement_service.create_document_requirement(
            rule_version_id=str(rule_version_unpublished.id),
            document_type_id=str(doc2.id),
            mandatory=True,
            conditional_logic=None,
        )
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/visa-document-requirements/bulk-operation/",
            {
                "document_requirement_ids": [str(visa_document_requirement.id), str(extra.id), str(uuid4())],
                "operation": "set_optional",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 2
        assert len(resp.data["data"]["failed"]) >= 1

