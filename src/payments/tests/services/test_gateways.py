import hmac
import hashlib
import json

import pytest

from payments.gateways.stripe_gateway import StripeGateway
from payments.gateways.paypal_gateway import PayPalGateway
from payments.gateways.adyen_gateway import AdyenGateway


@pytest.mark.django_db
class TestStripeGateway:
    def test_verify_payment_status_mapping(self, monkeypatch):
        # Configure gateway
        monkeypatch.setattr("payments.gateways.stripe_gateway.settings.STRIPE_SECRET_KEY", "sk_test")
        g = StripeGateway()

        monkeypatch.setattr(
            g,
            "_make_request",
            lambda method, endpoint, data=None: {
                "id": "pi_1",
                "status": "succeeded",
                "amount": 1234,
                "currency": "usd",
                "metadata": {"reference": "ref_1"},
                "charges": {"data": [{"paid": True, "created": 1700000000}]},
            },
        )
        res = g.verify_payment("pi_1")
        assert res["success"] is True
        assert res["status"] == "completed"
        assert str(res["amount"]) == "12.34"

    def test_webhook_signature_verification(self, monkeypatch):
        monkeypatch.setattr("payments.gateways.stripe_gateway.settings.STRIPE_SECRET_KEY", "sk_test")
        monkeypatch.setattr("payments.gateways.stripe_gateway.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
        g = StripeGateway()
        g.webhook_secret = "whsec_test"

        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_1", "amount": 1000, "currency": "usd", "metadata": {"reference": "ref"}}}}
        timestamp = "1700000000"
        signed_payload = f"{timestamp}.{json.dumps(payload, separators=(',', ':'))}"
        expected = hmac.new(b"whsec_test", signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        sig_header = f"t={timestamp},v1={expected}"
        assert g._verify_webhook_signature(payload, sig_header, headers={"stripe-signature": sig_header}) is True


class TestPayPalGateway:
    def test_webhook_signature_verification_checks_webhook_id_header(self, monkeypatch):
        monkeypatch.setattr("payments.gateways.paypal_gateway.settings.PAYPAL_CLIENT_ID", "cid")
        monkeypatch.setattr("payments.gateways.paypal_gateway.settings.PAYPAL_CLIENT_SECRET", "sec")
        monkeypatch.setattr("payments.gateways.paypal_gateway.settings.PAYPAL_WEBHOOK_ID", "wh_1")
        g = PayPalGateway()
        g.webhook_id = "wh_1"
        ok = g._verify_webhook_signature(payload={"event_type": "x"}, signature="sig", headers={"paypal-webhook-id": "wh_1"})
        assert ok is True
        ok2 = g._verify_webhook_signature(payload={"event_type": "x"}, signature="sig", headers={"paypal-webhook-id": "other"})
        assert ok2 is False


class TestAdyenGateway:
    def test_webhook_signature_verification(self, monkeypatch):
        monkeypatch.setattr("payments.gateways.adyen_gateway.settings.ADYEN_API_KEY", "key")
        monkeypatch.setattr("payments.gateways.adyen_gateway.settings.ADYEN_MERCHANT_ACCOUNT", "merchant")
        monkeypatch.setattr("payments.gateways.adyen_gateway.settings.ADYEN_HMAC_KEY", "hmac_key")
        g = AdyenGateway()
        g.hmac_key = "hmac_key"

        payload = {
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "merchantReference": "mref",
                        "originalReference": "oref",
                        "amount": {"currency": "USD", "value": 1000},
                        "eventCode": "AUTHORISATION",
                        "success": "true",
                    }
                }
            ]
        }
        data_string = "mref:oref:USD:1000:AUTHORISATION:true"
        expected = hmac.new(b"hmac_key", data_string.encode("utf-8"), hashlib.sha256).hexdigest()
        sig_header = f"hmacSignature={expected}"
        assert g._verify_webhook_signature(payload, signature=sig_header, headers={"adyen-signature": sig_header}) is True

