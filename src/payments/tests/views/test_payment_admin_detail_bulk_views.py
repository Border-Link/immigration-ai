from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework import status


BASE = "/api/v1/payments/admin"


@pytest.mark.django_db
class TestPaymentAdminDetailBulkViews:
    def test_admin_detail_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/payments/{uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_detail_update_delete_and_bulk(self, api_client, admin_user, payment_service, payment_owner):
        # Create a payment to manage
        payment = payment_service.create_payment(
            user_id=str(payment_owner.id),
            amount=Decimal("25.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_admin_001",
            changed_by=payment_owner,
        )
        assert payment is not None

        api_client.force_authenticate(user=admin_user)

        # Detail
        resp = api_client.get(f"{BASE}/payments/{payment.id}/")
        assert resp.status_code == status.HTTP_200_OK

        # Update
        resp2 = api_client.patch(
            f"{BASE}/payments/{payment.id}/update/",
            {"status": "processing", "version": 1},
            format="json",
        )
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data["data"]["status"] == "processing"

        # Bulk update status
        resp3 = api_client.post(
            f"{BASE}/payments/bulk-operation/",
            {"payment_ids": [str(payment.id)], "operation": "update_status", "status": "completed"},
            format="json",
        )
        assert resp3.status_code == status.HTTP_200_OK
        assert len(resp3.data["data"]["success"]) == 1

        # Delete
        resp4 = api_client.delete(f"{BASE}/payments/{payment.id}/delete/")
        assert resp4.status_code == status.HTTP_200_OK

    def test_bulk_update_status_requires_status(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{BASE}/payments/bulk-operation/",
            {"payment_ids": [str(uuid4())], "operation": "update_status"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

