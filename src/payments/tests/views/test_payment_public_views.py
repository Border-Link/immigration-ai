from rest_framework import status
import pytest


BASE = "/api/v1/payments"


@pytest.mark.django_db
class TestPaymentPublicViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{BASE}/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_only_own_payments_for_regular_user(self, api_client, payment_service, payment_owner, other_user):
        # Create payments for two users
        p1 = payment_service.create_payment(user_id=str(payment_owner.id), amount=10, currency="USD", payment_provider="stripe", changed_by=payment_owner)
        p2 = payment_service.create_payment(user_id=str(other_user.id), amount=20, currency="USD", payment_provider="stripe", changed_by=other_user)
        assert p1 and p2

        api_client.force_authenticate(user=payment_owner)
        resp = api_client.get(f"{BASE}/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(p1.id) in ids
        assert str(p2.id) not in ids

    def test_list_staff_sees_all(self, api_client, payment_service, admin_user, payment_owner):
        p1 = payment_service.create_payment(user_id=str(payment_owner.id), amount=10, currency="USD", payment_provider="stripe", changed_by=payment_owner)
        assert p1
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/")
        assert resp.status_code == status.HTTP_200_OK
        assert any(item["id"] == str(p1.id) for item in resp.data["data"])

    def test_create_payment_success(self, api_client, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        payload = {"user_id": str(payment_owner.id), "amount": "50.00", "currency": "USD", "payment_provider": "stripe"}
        resp = api_client.post(f"{BASE}/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["status"] == "pending"

    def test_create_payment_invalid_payload(self, api_client, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        # missing required amount/provider, and both ids missing
        resp = api_client.post(f"{BASE}/create/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_enforces_object_permission(self, api_client, payment_service, payment_owner, other_user):
        payment = payment_service.create_payment(user_id=str(payment_owner.id), amount=10, currency="USD", payment_provider="stripe", changed_by=payment_owner)
        assert payment
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"{BASE}/{payment.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

