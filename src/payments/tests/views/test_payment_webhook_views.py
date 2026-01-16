import json
from unittest.mock import MagicMock

import pytest
from rest_framework import status


BASE = "/api/v1/payments/webhooks"


@pytest.mark.django_db
class TestPaymentWebhookViews:
    def test_webhook_requires_signature_when_debug_false(self, api_client):
        resp = api_client.post(f"{BASE}/stripe/", {"type": "payment_intent.succeeded"}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_webhook_invalid_json_returns_400(self, api_client):
        resp = api_client.post(
            f"{BASE}/stripe/",
            data="not-json",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_processes_and_returns_200_on_failure_result(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.process_webhook",
            MagicMock(return_value={"success": False, "error": "ignored"}),
        )
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=False),
        )
        resp = api_client.post(
            f"{BASE}/stripe/",
            data=json.dumps({"type": "x"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_webhook_success(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.process_webhook",
            MagicMock(return_value={"success": True, "payment_id": "p1", "status": "completed"}),
        )
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=False),
        )
        resp = api_client.post(
            f"{BASE}/stripe/",
            data=json.dumps({"type": "payment_intent.succeeded"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "completed"

    def test_paypal_and_adyen_signature_headers_are_accepted(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.process_webhook",
            MagicMock(return_value={"success": True, "payment_id": "p1", "status": "completed"}),
        )
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=False),
        )

        resp_paypal = api_client.post(
            f"{BASE}/paypal/",
            data=json.dumps({"event_type": "x"}),
            content_type="application/json",
            HTTP_PAYPAL_TRANSMISSION_SIG="sig",
        )
        assert resp_paypal.status_code == status.HTTP_200_OK

        resp_adyen = api_client.post(
            f"{BASE}/adyen/",
            data=json.dumps({"notificationItems": []}),
            content_type="application/json",
            HTTP_ADYEN_SIGNATURE="sig",
        )
        assert resp_adyen.status_code == status.HTTP_200_OK

    def test_webhook_allows_missing_signature_when_debug_true(self, api_client, settings, monkeypatch):
        settings.DEBUG = True
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=False),
        )
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.process_webhook",
            MagicMock(return_value={"success": True, "payment_id": "p1", "status": "completed"}),
        )
        resp = api_client.post(
            f"{BASE}/stripe/",
            data=json.dumps({"type": "payment_intent.succeeded"}),
            content_type="application/json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_webhook_rate_limited_returns_429(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=True),
        )
        resp = api_client.post(
            f"{BASE}/stripe/",
            data=json.dumps({"type": "x"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig",
        )
        assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_webhook_payment_gateway_error_returns_400(self, api_client, monkeypatch):
        from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError

        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=False),
        )
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.process_webhook",
            MagicMock(side_effect=PaymentGatewayError("bad sig")),
        )
        resp = api_client.post(
            f"{BASE}/stripe/",
            data=json.dumps({"type": "x"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_unhandled_exception_returns_500(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.check_rate_limit",
            MagicMock(return_value=False),
        )
        monkeypatch.setattr(
            "payments.views.webhooks.base.PaymentWebhookService.process_webhook",
            MagicMock(side_effect=RuntimeError("boom")),
        )
        resp = api_client.post(
            f"{BASE}/stripe/",
            data=json.dumps({"type": "x"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig",
        )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

