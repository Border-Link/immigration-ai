"""
Admin API tests for document processing analytics/statistics endpoint.
"""

from __future__ import annotations

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/document-processing"


@pytest.mark.django_db
class TestDocumentProcessingStatisticsAPI:
    def test_requires_authentication(self, api_client):
        url = f"{API_PREFIX}/admin/statistics/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_admin(self, api_client, case_owner):
        url = f"{API_PREFIX}/admin/statistics/"
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_returns_combined_statistics(self, api_client, admin_user, processing_job_service, processing_history_service, case_document):
        processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/statistics/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert "processing_jobs" in resp.data["data"]
        assert "processing_history" in resp.data["data"]

