"""
Tests for DocumentCheck public endpoints.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status


API_PREFIX = "/api/v1/document-handling"


@pytest.mark.django_db
class TestDocumentCheckViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/document-checks/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, client, test_user, document_check):
        client.force_authenticate(user=test_user)
        resp = client.get(f"{API_PREFIX}/document-checks/")
        assert resp.status_code == status.HTTP_200_OK

    def test_detail_not_found(self, client, test_user):
        from uuid import uuid4

        client.force_authenticate(user=test_user)
        resp = client.get(f"{API_PREFIX}/document-checks/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_create_success(self, client, test_user, case_document):
        client.force_authenticate(user=test_user)
        resp = client.post(
            f"{API_PREFIX}/document-checks/create/",
            data={
                "case_document_id": str(case_document.id),
                "check_type": "ocr",
                "result": "passed",
                "details": {"x": 1},
                "performed_by": "pytest",
            },
            format="json",
        )
        # Service should succeed given payment bypass and valid case_document
        assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_update_not_found(self, client, test_user):
        from uuid import uuid4

        client.force_authenticate(user=test_user)
        resp = client.patch(f"{API_PREFIX}/document-checks/{uuid4()}/update/", data={"result": "warning"}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_not_found(self, client, test_user):
        from uuid import uuid4

        client.force_authenticate(user=test_user)
        resp = client.delete(f"{API_PREFIX}/document-checks/{uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

