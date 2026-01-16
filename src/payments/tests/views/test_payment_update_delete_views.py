from rest_framework import status
import pytest


BASE = "/api/v1/payments"


@pytest.mark.django_db
class TestPaymentUpdateDeleteViews:
    def test_update_requires_auth(self, api_client, pre_case_payment_pending):
        resp = api_client.patch(f"{BASE}/{pre_case_payment_pending.id}/update/", {"status": "processing"}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_forbidden_for_non_owner(self, api_client, pre_case_payment_pending, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.patch(f"{BASE}/{pre_case_payment_pending.id}/update/", {"status": "processing"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_success_for_owner(self, api_client, pre_case_payment_pending, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.patch(f"{BASE}/{pre_case_payment_pending.id}/update/", {"status": "processing", "version": 1}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "processing"

    def test_delete_forbidden_for_non_owner(self, api_client, pre_case_payment_pending, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.delete(f"{BASE}/{pre_case_payment_pending.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_success_for_owner(self, api_client, pre_case_payment_pending, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.delete(f"{BASE}/{pre_case_payment_pending.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

