from unittest.mock import MagicMock

import pytest
from rest_framework import status


BASE = "/api/v1/payments"


@pytest.mark.django_db
class TestPaymentGatewayViews:
    def test_initiate_forbidden_for_non_owner(self, api_client, pre_case_payment_with_txn_pending, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.post(f"{BASE}/{pre_case_payment_with_txn_pending.id}/initiate/", {}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_initiate_success_for_owner_with_mocked_gateway(self, api_client, monkeypatch, pre_case_payment_with_txn_pending, payment_owner):
        monkeypatch.setattr(
            "payments.services.payment_service.PaymentGatewayService.initialize_payment",
            MagicMock(return_value={"success": True, "transaction_id": "txn_new", "payment_url": "https://example.test"}),
        )
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(
            f"{BASE}/{pre_case_payment_with_txn_pending.id}/initiate/",
            {"return_url": "https://return.test"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["transaction_id"] == "txn_new"

    def test_verify_requires_provider_and_transaction(self, api_client, payment_owner, pre_case_payment_pending):
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(f"{BASE}/{pre_case_payment_pending.id}/verify/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_success_updates_status(self, api_client, monkeypatch, payment_owner, pre_case_payment_with_txn_pending):
        monkeypatch.setattr(
            "payments.services.payment_service.PaymentGatewayService.verify_payment",
            MagicMock(return_value={"success": True, "status": "completed"}),
        )
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(f"{BASE}/{pre_case_payment_with_txn_pending.id}/verify/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["verification"]["status"] == "completed"

    def test_refund_forbidden_for_non_owner(self, api_client, pre_case_payment_completed, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.post(f"{BASE}/{pre_case_payment_completed.id}/refund/", {}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_refund_success(self, api_client, monkeypatch, pre_case_payment_completed, payment_owner):
        monkeypatch.setattr(
            "payments.services.payment_service.PaymentGatewayService.refund_payment",
            MagicMock(return_value={"success": True, "refund_id": "ref_1", "status": "completed"}),
        )
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(f"{BASE}/{pre_case_payment_completed.id}/refund/", {"reason": "dup"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["refund"]["refund_id"] == "ref_1"

