"""
Tests for document_handling admin endpoints.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch


API_PREFIX = "/api/v1/document-handling"


@pytest.mark.django_db
class TestDocumentHandlingAdminViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_admin_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/admin/case-documents/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_forbidden_for_non_staff(self, client, test_user):
        client.force_authenticate(user=test_user)
        resp = client.get(f"{API_PREFIX}/admin/case-documents/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success_for_staff(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/admin/case-documents/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_document_checks_list_success_for_staff(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/admin/document-checks/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_statistics_success_for_staff(self, client, admin_user):
        client.force_authenticate(user=admin_user)
        resp = client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "data" in resp.data

    @patch("document_handling.views.admin.case_document_admin.DocumentReprocessingService.reprocess_ocr")
    def test_admin_bulk_operation_reprocess_ocr(self, mock_reprocess, client, admin_user, case_document):
        client.force_authenticate(user=admin_user)
        mock_reprocess.return_value = True
        resp = client.post(
            f"{API_PREFIX}/admin/case-documents/bulk-operation/",
            data={"document_ids": [str(case_document.id)], "operation": "reprocess_ocr"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        mock_reprocess.assert_called_once()

    def test_admin_bulk_operation_update_status_missing_status_returns_400(self, client, admin_user, case_document):
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/admin/case-documents/bulk-operation/",
            data={"document_ids": [str(case_document.id)], "operation": "update_status"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_bulk_operation_unknown_returns_400(self, client, admin_user, case_document):
        client.force_authenticate(user=admin_user)
        resp = client.post(
            f"{API_PREFIX}/admin/case-documents/bulk-operation/",
            data={"document_ids": [str(case_document.id)], "operation": "unknown"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

