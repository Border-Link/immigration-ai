"""
Admin API tests for case management endpoints.
"""

from decimal import Decimal

import pytest
from rest_framework import status


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestAdminCaseEndpoints:
    def test_admin_list_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/admin/cases/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, api_client, admin_user, draft_case):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/cases/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(draft_case.id) in ids

    def test_admin_detail_success(self, api_client, admin_user, draft_case):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/admin/cases/{draft_case.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(draft_case.id)

    def test_admin_update_status_closed_does_not_require_payment(self, api_client, case_service, admin_user, draft_case):
        api_client.force_authenticate(user=admin_user)
        current = case_service.get_by_id(str(draft_case.id))
        resp = api_client.patch(
            f"{BASE}/admin/cases/{draft_case.id}/update/",
            {"status": "closed", "version": current.version, "reason": "archive"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "closed"

    def test_admin_delete_unpaid_returns_400(self, api_client, admin_user, case_without_completed_payment):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{BASE}/admin/cases/{case_without_completed_payment.id}/delete/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_bulk_delete_mixed_results(self, api_client, case_service, payment_service, admin_user, case_owner, other_user):
        # paid user -> paid case
        p_paid = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_bulk_001",
            plan="basic",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p_paid.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p_paid.id), status="completed", changed_by=other_user, reason="complete")
        paid = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        assert paid is not None

        # "unpaid" case (simulate by creating valid case then deleting its payment)
        p_unpaid = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_bulk_002",
            plan="basic",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(p_unpaid.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(p_unpaid.id), status="completed", changed_by=case_owner, reason="complete")
        unpaid = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        assert unpaid is not None
        # delete attached payment so delete operation fails
        from payments.services.payment_service import PaymentService as _PS
        attached = _PS.get_by_case(str(unpaid.id)).filter(status="completed").first()
        assert attached is not None
        _PS.delete_payment(payment_id=str(attached.id), changed_by=case_owner, reason="test delete", hard_delete=False)
        from payments.helpers.payment_validator import PaymentValidator
        PaymentValidator.invalidate_payment_cache(str(unpaid.id))

        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{BASE}/admin/cases/bulk-operation/",
            {"case_ids": [str(unpaid.id), str(paid.id)], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) == 1
        assert len(resp.data["data"]["failed"]) == 1

    def test_admin_bulk_update_status_requires_status_field(self, api_client, admin_user, draft_case):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{BASE}/admin/cases/bulk-operation/",
            {"case_ids": [str(draft_case.id)], "operation": "update_status"},
            format="json",
        )
        # BaseBulkOperationAPI always returns 200 with per-entity failure info
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["failed"]) == 1

