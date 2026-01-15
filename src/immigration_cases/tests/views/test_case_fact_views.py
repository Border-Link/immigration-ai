"""
API tests for case fact endpoints in `immigration_cases`.
"""

from decimal import Decimal

import pytest
from rest_framework import status


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestCaseFactEndpoints:
    def test_create_requires_auth(self, api_client, paid_case):
        case, _payment = paid_case
        resp = api_client.post(
            f"{BASE}/case-facts/create/",
            {"case_id": str(case.id), "fact_key": "age", "fact_value": 30, "source": "user"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_success(self, api_client, case_owner, paid_case):
        case, _payment = paid_case
        api_client.force_authenticate(user=case_owner)
        payload = {"case_id": str(case.id), "fact_key": "age", "fact_value": 30, "source": "user"}
        resp = api_client.post(f"{BASE}/case-facts/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["fact_key"] == "age"
        assert resp.data["data"]["fact_value"] == 30

    def test_create_for_other_users_case_forbidden(self, api_client, case_service, case_owner, other_user, payment_service):
        # Prepay other user then create their case
        p = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_test_other",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=other_user, reason="complete")
        other_case = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        assert other_case is not None

        api_client.force_authenticate(user=case_owner)
        payload = {"case_id": str(other_case.id), "fact_key": "age", "fact_value": 30, "source": "user"}
        resp = api_client.post(f"{BASE}/case-facts/create/", payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_requires_payment(self, api_client, case_owner, case_without_completed_payment):
        api_client.force_authenticate(user=case_owner)
        payload = {"case_id": str(case_without_completed_payment.id), "fact_key": "age", "fact_value": 30, "source": "user"}
        resp = api_client.post(f"{BASE}/case-facts/create/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_requires_case_id_for_non_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/case-facts/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "case_id is required" in (resp.data.get("message") or "").lower()

    def test_list_by_case_success(self, api_client, case_owner, paid_case_with_fact):
        case, fact = paid_case_with_fact
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/case-facts/?case_id={case.id}")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(fact.id) in ids

    def test_detail_other_users_fact_forbidden(self, api_client, case_service, case_fact_service, payment_service, case_owner, other_user):
        p = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_test_other2",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=other_user, reason="complete")
        other_case = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        assert other_case is not None
        other_fact = case_fact_service.create_case_fact(str(other_case.id), "age", 30, "user")

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/case-facts/{other_fact.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_and_delete_success(self, api_client, case_owner, case_fact_service, paid_case_with_fact):
        case, fact = paid_case_with_fact
        api_client.force_authenticate(user=case_owner)

        resp = api_client.patch(
            f"{BASE}/case-facts/{fact.id}/update/",
            {"fact_value": 31},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["fact_value"] == 31

        resp_del = api_client.delete(f"{BASE}/case-facts/{fact.id}/delete/")
        assert resp_del.status_code == status.HTTP_200_OK

        # Deleted -> service should return None -> API 404
        resp_get = api_client.get(f"{BASE}/case-facts/{fact.id}/")
        assert resp_get.status_code == status.HTTP_404_NOT_FOUND

