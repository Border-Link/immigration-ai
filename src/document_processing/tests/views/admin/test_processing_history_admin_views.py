"""
Admin API tests for ProcessingHistory views.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/document-processing"


@pytest.mark.django_db
class TestProcessingHistoryAdminListAPI:
    def test_list_requires_authentication(self, api_client):
        url = f"{API_PREFIX}/admin/processing-history/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_requires_admin(self, api_client, case_owner):
        url = f"{API_PREFIX}/admin/processing-history/"
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_success_and_filters(self, api_client, admin_user, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/"
        resp = api_client.get(url, {"case_document_id": str(case_document.id), "action": "job_created"})
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(entry.id) in ids

    def test_list_invalid_query_returns_400(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/"
        resp = api_client.get(url, {"case_document_id": "not-a-uuid"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp2 = api_client.get(url, {"limit": 0})
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProcessingHistoryAdminDetailAPI:
    def test_get_detail_success(self, api_client, admin_user, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/{entry.id}/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(entry.id)

    def test_get_detail_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/{uuid4()}/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProcessingHistoryAdminDeleteAPI:
    def test_delete_success(self, api_client, admin_user, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/{entry.id}/delete/"
        resp = api_client.delete(url)
        assert resp.status_code == status.HTTP_200_OK

    def test_delete_blocked_without_payment_returns_400(
        self,
        api_client,
        admin_user,
        user_service,
        case_service,
        payment_service,
        document_type_service,
        case_document_service,
        processing_history_service,
        monkeypatch,
    ):
        """
        Ensure the delete endpoint honors ProcessingHistoryService payment validation.
        We build a fully valid paid case/document/history, then soft-delete the payment and invalidate cache.
        """
        owner = user_service.create_user(email="dp-history-owner@example.com", password="OwnerPass123!@#")
        assert owner is not None

        payment = payment_service.create_payment(
            user_id=str(owner.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_dp_hist_001",
            changed_by=owner,
        )
        assert payment is not None
        payment = payment_service.update_payment(str(payment.id), status="processing", changed_by=owner, reason="processing")
        assert payment is not None
        payment = payment_service.update_payment(str(payment.id), status="completed", changed_by=owner, reason="done")
        assert payment is not None
        case = case_service.create_case(user_id=str(owner.id), jurisdiction="US", status="draft")
        assert case is not None

        doc_type = document_type_service.create_document_type(code="DP_HIST_DOC", name="DP Hist Doc", is_active=True)
        assert doc_type is not None

        doc = case_document_service.create_case_document(
            case_id=str(case.id),
            document_type_id=str(doc_type.id),
            file_path="case_documents/dp_tests/hist.pdf",
            file_name="hist.pdf",
            file_size=100,
            mime_type="application/pdf",
            status="uploaded",
        )
        assert doc is not None

        entry = processing_history_service.create_history_entry(
            case_document_id=str(doc.id),
            action="job_created",
            status="success",
        )
        assert entry is not None

        # Now soft-delete payment and invalidate cache so the case is blocked
        deleted = payment_service.delete_payment(str(payment.id), changed_by=owner, reason="test", hard_delete=False)
        assert deleted is True
        from payments.helpers.payment_validator import PaymentValidator

        PaymentValidator.invalidate_payment_cache(str(case.id))

        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/{entry.id}/delete/"
        resp = api_client.delete(url)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBulkProcessingHistoryOperationAPI:
    def test_bulk_delete_success_and_not_found(self, api_client, admin_user, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/bulk-operation/"
        resp = api_client.post(
            url,
            {"history_ids": [str(entry.id), str(uuid4())], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) == 1
        assert len(resp.data["data"]["failed"]) == 1

    def test_bulk_delete_validation(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = f"{API_PREFIX}/admin/processing-history/bulk-operation/"
        resp = api_client.post(url, {"history_ids": [], "operation": "delete"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

