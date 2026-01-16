"""
Admin API tests for ProcessingJob views.

Constraints:
- Authenticate using APIClient.force_authenticate
- Create state via services (no direct model access)
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/document-processing"


@pytest.mark.django_db
class TestProcessingJobAdminListAPI:
    def test_requires_authentication(self, api_client):
        url = f"{API_PREFIX}/admin/processing-jobs/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_admin(self, api_client, case_owner):
        url = f"{API_PREFIX}/admin/processing-jobs/"
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_jobs_success(self, api_client, admin_user, processing_job_service, case_document):
        processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert "data" in resp.data

    def test_list_jobs_with_filters_and_validation(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", priority=5
        )
        processing_job_service.update_status(str(job.id), "queued")

        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/"
        resp = api_client.get(
            url,
            {
                "case_document_id": str(case_document.id),
                "status": "queued",
                "processing_type": "ocr",
                "min_priority": "1",
                "max_retries_exceeded": "false",
            },
        )
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(job.id) in ids

    def test_list_jobs_invalid_query_returns_400(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/"
        resp = api_client.get(url, {"case_document_id": "not-a-uuid"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp2 = api_client.get(url, {"min_priority": 11})
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProcessingJobAdminDetailAPI:
    def test_get_detail_success(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{job.id}/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(job.id)

    def test_get_detail_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{uuid4()}/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProcessingJobAdminUpdateAPI:
    def test_patch_update_success(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{job.id}/update/"
        resp = api_client.patch(url, {"priority": 10}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["priority"] == 10

    def test_put_update_success(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{job.id}/update/"
        resp = api_client.put(url, {"priority": 8}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["priority"] == 8

    def test_update_invalid_status_transition_returns_400(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{job.id}/update/"
        resp = api_client.patch(url, {"status": "completed"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_not_found_returns_404(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{uuid4()}/update/"
        resp = api_client.patch(url, {"priority": 2}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProcessingJobAdminDeleteAPI:
    def test_delete_success(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{job.id}/delete/"
        resp = api_client.delete(url)
        assert resp.status_code == status.HTTP_200_OK

    def test_delete_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/{uuid4()}/delete/"
        resp = api_client.delete(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestBulkProcessingJobOperationAPI:
    def test_bulk_delete_counts(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/bulk-operation/"
        resp = api_client.post(
            url,
            {"job_ids": [str(job.id), str(uuid4())], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["deleted_count"] == 1
        assert resp.data["data"]["failed_count"] == 1

    def test_bulk_cancel_counts(self, api_client, admin_user, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/bulk-operation/"
        resp = api_client.post(url, {"job_ids": [str(job.id)], "operation": "cancel"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        updated = processing_job_service.get_by_id(str(job.id))
        assert updated.status == "cancelled"

    def test_bulk_retry_counts(self, api_client, admin_user, processing_job_service, case_document):
        eligible = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=2
        )
        ineligible = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=1
        )
        for job in (eligible, ineligible):
            processing_job_service.update_status(str(job.id), "queued")
            processing_job_service.update_status(str(job.id), "processing")
            processing_job_service.update_status(str(job.id), "failed")
        processing_job_service.update_processing_job(str(ineligible.id), retry_count=1)

        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/bulk-operation/"
        resp = api_client.post(
            url,
            {"job_ids": [str(eligible.id), str(ineligible.id)], "operation": "retry"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["retried_count"] == 1
        assert resp.data["data"]["failed_count"] == 1

    def test_bulk_update_status_requires_status(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/bulk-operation/"
        resp = api_client.post(url, {"job_ids": [str(uuid4())], "operation": "update_status"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_update_priority_requires_priority(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/bulk-operation/"
        resp = api_client.post(url, {"job_ids": [str(uuid4())], "operation": "update_priority"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_unknown_operation_branch_defensive(self, api_client, admin_user, monkeypatch):
        """
        The serializer prevents unknown operations, but the view has a defensive 'else' branch.
        We force that branch by monkeypatching the serializer used by the view.
        """
        from document_processing.views.admin import processing_job_admin as view_module

        class _FakeSerializer:
            def __init__(self, data=None, **_kwargs):
                self._data = data or {}
                self.validated_data = {}

            def is_valid(self, raise_exception=False):
                self.validated_data = {"job_ids": [uuid4()], "operation": "unknown"}
                return True

        monkeypatch.setattr(view_module, "BulkProcessingJobOperationSerializer", _FakeSerializer, raising=True)

        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-jobs/bulk-operation/"
        resp = api_client.post(url, {"job_ids": [str(uuid4())], "operation": "delete"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

