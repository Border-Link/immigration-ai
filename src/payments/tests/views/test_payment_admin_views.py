from rest_framework import status
import pytest


BASE = "/api/v1/payments/admin"


@pytest.mark.django_db
class TestPaymentAdminViews:
    def test_admin_list_requires_admin(self, api_client, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.get(f"{BASE}/payments/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/payments/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_statistics_requires_admin(self, api_client, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.get(f"{BASE}/statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_statistics_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "total_payments" in resp.data["data"]

