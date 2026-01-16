from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from payments.services.payment_webhook_service import PaymentWebhookService
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError


@pytest.mark.django_db
class TestPaymentWebhookService:
    def test_process_webhook_gateway_error_returns_failure(self, monkeypatch):
        monkeypatch.setattr(
            "payments.services.payment_webhook_service.PaymentGatewayService.process_webhook",
            MagicMock(side_effect=PaymentGatewayError("bad sig")),
        )
        res = PaymentWebhookService.process_webhook(provider="stripe", payload={"x": 1}, signature="sig", headers={})
        assert res["success"] is False
        assert "bad sig" in res["error"]

    def test_update_payment_from_webhook_missing_reference(self):
        res = PaymentWebhookService._update_payment_from_webhook(provider="stripe", webhook_result={"status": "completed"})
        assert res["success"] is False

    def test_update_payment_from_webhook_payment_not_found(self):
        res = PaymentWebhookService._update_payment_from_webhook(
            provider="stripe",
            webhook_result={"reference": "00000000-0000-0000-0000-000000000000", "status": "completed"},
        )
        assert res["success"] is False

    def test_update_payment_from_webhook_amount_mismatch_blocks(self, pre_case_payment_pending):
        res = PaymentWebhookService._update_payment_from_webhook(
            provider="stripe",
            webhook_result={
                "reference": str(pre_case_payment_pending.id),
                "transaction_id": "txn_x",
                "event_type": "payment.completed",
                "status": "completed",
                "amount": Decimal("999.99"),
            },
        )
        assert res["success"] is False
        assert "amount mismatch" in res["error"].lower()

    def test_update_payment_from_webhook_idempotency_skips_second_time(self, monkeypatch, pre_case_payment_pending):
        # First call should create webhook event and attempt status update.
        monkeypatch.setattr(
            "payments.services.payment_webhook_service.PaymentService.update_payment",
            MagicMock(return_value=pre_case_payment_pending),
        )
        first = PaymentWebhookService._update_payment_from_webhook(
            provider="stripe",
            webhook_result={
                "reference": str(pre_case_payment_pending.id),
                "event_id": "evt_1",
                "event_type": "payment.completed",
                "status": "completed",
                "amount": Decimal("100.00"),
                "transaction_id": "txn_1",
            },
        )
        assert first["success"] is True

        # Second call with same event_id should short-circuit.
        second = PaymentWebhookService._update_payment_from_webhook(
            provider="stripe",
            webhook_result={
                "reference": str(pre_case_payment_pending.id),
                "event_id": "evt_1",
                "event_type": "payment.completed",
                "status": "completed",
                "amount": Decimal("100.00"),
                "transaction_id": "txn_1",
            },
        )
        assert second["success"] is True
        assert "already" in second.get("message", "").lower()

    def test_rate_limit_counts_requests(self):
        # First N calls should not be rate limited
        assert PaymentWebhookService.check_rate_limit("stripe", "127.0.0.1", max_requests=2, window_seconds=60) is False
        assert PaymentWebhookService.check_rate_limit("stripe", "127.0.0.1", max_requests=2, window_seconds=60) is False
        assert PaymentWebhookService.check_rate_limit("stripe", "127.0.0.1", max_requests=2, window_seconds=60) is True

