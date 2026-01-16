from unittest.mock import MagicMock

import pytest
from rest_framework import status


BASE = "/api/v1/payments"


@pytest.mark.django_db
class TestPaymentHistoryAndRetryViews:
    def test_history_requires_auth(self, api_client, paid_case):
        _case, payment = paid_case
        resp = api_client.get(f"{BASE}/{payment.id}/history/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_history_success_for_owner(self, api_client, paid_case, payment_owner):
        _case, payment = paid_case
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.get(f"{BASE}/{payment.id}/history/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)

    def test_retry_forbidden_for_non_owner(self, api_client, pre_case_payment_failed, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.post(f"{BASE}/{pre_case_payment_failed.id}/retry/", {}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_retry_success_for_owner_with_mocked_retry_service(self, api_client, monkeypatch, pre_case_payment_failed, payment_owner):
        monkeypatch.setattr(
            "payments.services.payment_retry_service.PaymentRetryService.retry_payment",
            MagicMock(return_value={"success": True, "retry_count": 1}),
        )
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(f"{BASE}/{pre_case_payment_failed.id}/retry/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["retry_result"]["success"] is True

