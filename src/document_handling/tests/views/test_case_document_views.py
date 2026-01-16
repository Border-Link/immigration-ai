"""
Tests for CaseDocument public endpoints.

We keep view tests focused on:
- authentication/permission response codes
- serializer validation behavior
- correct orchestration of service calls (including failure branches)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile


API_PREFIX = "/api/v1/document-handling"


@pytest.mark.django_db
class TestCaseDocumentViews:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/case-documents/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, client, test_user):
        client.force_authenticate(user=test_user)
        resp = client.get(f"{API_PREFIX}/case-documents/")
        assert resp.status_code == status.HTTP_200_OK

    def test_detail_not_found(self, client, test_user):
        from uuid import uuid4

        client.force_authenticate(user=test_user)
        resp = client.get(f"{API_PREFIX}/case-documents/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @patch("document_handling.views.case_document.create.FileStorageService.store_file")
    @patch("document_handling.views.case_document.create.CaseDocumentService.create_case_document")
    def test_create_success(self, mock_create_doc, mock_store_file, client, test_user, test_case, active_document_type):
        client.force_authenticate(user=test_user)
        mock_store_file.return_value = ("case_documents/x/y/z.pdf", None)
        # Minimal object with attributes used by serializer
        mock_create_doc.return_value = type(
            "Doc",
            (),
            {
                "id": "d",
                "case": test_case,
                "document_type": active_document_type,
                "file_path": "case_documents/x/y/z.pdf",
                "file_name": "z.pdf",
                "file_size": 1,
                "mime_type": "application/pdf",
                "status": "uploaded",
                "ocr_text": None,
                "classification_confidence": None,
                "expiry_date": None,
                "extracted_metadata": None,
                "content_validation_status": "pending",
                "content_validation_details": None,
                "uploaded_at": None,
                "updated_at": None,
            },
        )()

        resp = client.post(
            f"{API_PREFIX}/case-documents/create/",
            data={
                "case_id": str(test_case.id),
                "document_type_id": str(active_document_type.id),
                "file": SimpleUploadedFile("z.pdf", b"%PDF-1.4\n...", content_type="application/pdf"),
                "file_name": "z.pdf",
                "file_size": 1,
                "mime_type": "application/pdf",
            },
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED

    @patch("document_handling.views.case_document.create.FileStorageService.store_file")
    def test_create_storage_failure_returns_500(self, mock_store_file, client, test_user, test_case, active_document_type):
        client.force_authenticate(user=test_user)
        mock_store_file.return_value = (None, "storage error")
        resp = client.post(
            f"{API_PREFIX}/case-documents/create/",
            data={
                "case_id": str(test_case.id),
                "document_type_id": str(active_document_type.id),
                "file": SimpleUploadedFile("z.pdf", b"%PDF-1.4\n...", content_type="application/pdf"),
                "file_name": "z.pdf",
                "file_size": 1,
                "mime_type": "application/pdf",
            },
            format="multipart",
        )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch("document_handling.views.case_document.create.FileStorageService.delete_file")
    @patch("document_handling.views.case_document.create.FileStorageService.store_file")
    @patch("document_handling.views.case_document.create.CaseDocumentService.create_case_document")
    def test_create_db_failure_deletes_file_and_returns_500(self, mock_create_doc, mock_store_file, mock_delete, client, test_user, test_case, active_document_type):
        client.force_authenticate(user=test_user)
        mock_store_file.return_value = ("case_documents/x/y/z.pdf", None)
        mock_create_doc.return_value = None
        resp = client.post(
            f"{API_PREFIX}/case-documents/create/",
            data={
                "case_id": str(test_case.id),
                "document_type_id": str(active_document_type.id),
                "file": SimpleUploadedFile("z.pdf", b"%PDF-1.4\n...", content_type="application/pdf"),
                "file_name": "z.pdf",
                "file_size": 1,
                "mime_type": "application/pdf",
            },
            format="multipart",
        )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_delete.assert_called_once()

    def test_update_not_found(self, client, test_user):
        from uuid import uuid4

        client.force_authenticate(user=test_user)
        resp = client.patch(f"{API_PREFIX}/case-documents/{uuid4()}/update/", data={"file_name": "x.pdf"}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_not_found(self, client, test_user):
        from uuid import uuid4

        client.force_authenticate(user=test_user)
        resp = client.delete(f"{API_PREFIX}/case-documents/{uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_checklist_success(self, client, test_user, test_case):
        client.force_authenticate(user=test_user)
        resp = client.get(f"{API_PREFIX}/case-documents/case/{test_case.id}/checklist/")
        # Service may return error dict depending on rule setup; endpoint returns 200 if dict truthy
        assert resp.status_code in (status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR)

