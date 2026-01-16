from unittest.mock import MagicMock

import pytest

from payments.services.payment_retry_service import PaymentRetryService


@pytest.mark.django_db
class TestPaymentRetryService:
    def test_can_retry_only_failed_and_below_max(self, pre_case_payment_failed):
        assert PaymentRetryService.can_retry(pre_case_payment_failed) is True
        pre_case_payment_failed.retry_count = pre_case_payment_failed.max_retries
        assert PaymentRetryService.can_retry(pre_case_payment_failed) is False
        pre_case_payment_failed.status = "pending"
        assert PaymentRetryService.can_retry(pre_case_payment_failed) is False

    def test_retry_payment_not_found_returns_none(self, monkeypatch):
        monkeypatch.setattr("payments.services.payment_retry_service.PaymentSelector.get_by_id", MagicMock(return_value=None))
        assert PaymentRetryService.retry_payment("missing") is None

    def test_retry_payment_not_retryable_returns_reason(self, pre_case_payment_failed):
        pre_case_payment_failed.retry_count = pre_case_payment_failed.max_retries
        pre_case_payment_failed.save()
        res = PaymentRetryService.retry_payment(str(pre_case_payment_failed.id))
        assert res is not None
        assert res["success"] is False
        assert res["reason"] == "max_retries_reached"

    def test_retry_payment_success_with_gateway_sets_processing(self, monkeypatch, pre_case_payment_failed):
        monkeypatch.setattr(
            "payments.services.payment_retry_service.PaymentGatewayService.initialize_payment",
            MagicMock(return_value={"success": True, "transaction_id": "txn_retry", "payment_url": "https://example.test"}),
        )
        update_mock = MagicMock()
        monkeypatch.setattr("payments.services.payment_retry_service.PaymentService.update_payment", update_mock)

        res = PaymentRetryService.retry_payment(str(pre_case_payment_failed.id))
        assert res is not None and res["success"] is True
        update_mock.assert_called()

    def test_retry_payment_gateway_error_sets_failed(self, monkeypatch, pre_case_payment_failed):
        from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError

        monkeypatch.setattr(
            "payments.services.payment_retry_service.PaymentGatewayService.initialize_payment",
            MagicMock(side_effect=PaymentGatewayError("boom")),
        )
        update_mock = MagicMock()
        monkeypatch.setattr("payments.services.payment_retry_service.PaymentService.update_payment", update_mock)
        res = PaymentRetryService.retry_payment(str(pre_case_payment_failed.id))
        assert res is not None and res["success"] is False
        assert "boom" in res["error"]
        update_mock.assert_called()

