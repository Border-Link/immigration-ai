import pytest
from rest_framework import status


BASE = "/api/v1/payments/admin/pricing"


@pytest.mark.django_db
class TestPricingAdminViews:
    def test_list_requires_admin(self, api_client, payment_owner):
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.get(f"{BASE}/items/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_and_update_item_and_prices(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)

        # Create a plan item
        resp = api_client.post(
            f"{BASE}/items/",
            {
                "kind": "plan",
                "code": "basic",
                "name": "Basic Plan",
                "description": "basic plan",
                "is_active": True,
                "includes_ai_calls": False,
                "includes_human_review": False,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        item_id = resp.data["data"]["id"]

        # Upsert a price
        resp2 = api_client.post(
            f"{BASE}/items/{item_id}/prices/",
            {"currency": "USD", "amount": "111.11"},
            format="json",
        )
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data["data"]["currency"] == "USD"

        # List prices
        resp3 = api_client.get(f"{BASE}/items/{item_id}/prices/")
        assert resp3.status_code == status.HTTP_200_OK
        assert any(p["currency"] == "USD" for p in resp3.data["data"])

        # Update entitlements flags
        resp4 = api_client.patch(
            f"{BASE}/items/{item_id}/update/",
            {"includes_ai_calls": True},
            format="json",
        )
        assert resp4.status_code == status.HTTP_200_OK
        assert resp4.data["data"]["includes_ai_calls"] is True

        # Delete price
        resp5 = api_client.delete(f"{BASE}/items/{item_id}/prices/USD/delete/")
        assert resp5.status_code == status.HTTP_200_OK

