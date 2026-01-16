from unittest.mock import MagicMock

import pytest

from payments.services.payment_gateway_service import PaymentGatewayService
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError


class _DummyGateway:
    def __init__(self, configured=True):
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def get_provider_name(self) -> str:
        return "dummy"

    def initialize_payment(self, **kwargs):
        return {"success": True, "transaction_id": "txn_dummy", "payment_url": "https://example.test", "reference": kwargs["reference"]}

    def verify_payment(self, transaction_id: str):
        return {"success": True, "status": "completed", "transaction_id": transaction_id}

    def process_webhook(self, payload, signature=None, headers=None):
        return {"event_type": "payment.completed", "transaction_id": "txn_dummy", "reference": payload.get("reference"), "status": "completed"}

    def refund_payment(self, transaction_id: str, amount=None, reason=None):
        return {"success": True, "refund_id": "ref_1", "status": "completed", "amount": amount or 0}


@pytest.mark.django_db
class TestPaymentGatewayService:
    def test_get_gateway_unknown_provider_returns_none(self, monkeypatch):
        PaymentGatewayService._gateway_instances = {}
        assert PaymentGatewayService.get_gateway("nope") is None

    def test_get_gateway_not_configured_returns_none(self, monkeypatch):
        PaymentGatewayService._gateway_instances = {}
        monkeypatch.setattr(PaymentGatewayService, "GATEWAY_CLASSES", {"dummy": lambda: _DummyGateway(configured=False)})
        assert PaymentGatewayService.get_gateway("dummy") is None

    def test_get_gateway_caches_instance(self, monkeypatch):
        PaymentGatewayService._gateway_instances = {}
        factory = MagicMock(side_effect=lambda: _DummyGateway(configured=True))
        monkeypatch.setattr(PaymentGatewayService, "GATEWAY_CLASSES", {"dummy": factory})
        g1 = PaymentGatewayService.get_gateway("dummy")
        g2 = PaymentGatewayService.get_gateway("dummy")
        assert g1 is not None and g2 is not None
        assert g1 is g2
        assert factory.call_count == 1

    def test_get_available_providers_only_returns_configured(self, monkeypatch):
        PaymentGatewayService._gateway_instances = {}
        monkeypatch.setattr(
            PaymentGatewayService,
            "GATEWAY_CLASSES",
            {"a": lambda: _DummyGateway(configured=True), "b": lambda: _DummyGateway(configured=False)},
        )
        assert PaymentGatewayService.get_available_providers() == ["a"]

    def test_initialize_payment_requires_provider(self, pre_case_payment_pending):
        pre_case_payment_pending.payment_provider = None
        with pytest.raises(PaymentGatewayError):
            PaymentGatewayService.initialize_payment(pre_case_payment_pending)

    def test_refund_payment_requires_completed(self, pre_case_payment_pending):
        pre_case_payment_pending.provider_transaction_id = "txn_x"
        pre_case_payment_pending.payment_provider = "stripe"
        with pytest.raises(PaymentGatewayError):
            PaymentGatewayService.refund_payment(pre_case_payment_pending)

