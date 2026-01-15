"""
API tests for case endpoints in `immigration_cases`.
"""

import pytest
from rest_framework import status


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestCaseEndpoints:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{BASE}/cases/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_case_without_payment_fails(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        payload = {"user_id": str(case_owner.id), "jurisdiction": "US", "status": "draft"}
        resp = api_client.post(f"{BASE}/cases/create/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_case_success_with_payment(self, api_client, payment_service, case_owner):
        # Create & complete pre-case payment
        payment = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_case_api_001",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(payment.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(payment.id), status="completed", changed_by=case_owner, reason="complete")

        api_client.force_authenticate(user=case_owner)
        payload = {"user_id": str(case_owner.id), "jurisdiction": "US", "status": "draft"}
        resp = api_client.post(f"{BASE}/cases/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["jurisdiction"] == "US"
        assert str(resp.data["data"]["user"]) == str(case_owner.id)

    def test_create_case_for_other_user_forbidden(self, api_client, case_owner, other_user):
        api_client.force_authenticate(user=case_owner)
        payload = {"user_id": str(other_user.id), "jurisdiction": "US", "status": "draft"}
        resp = api_client.post(f"{BASE}/cases/create/", payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_cases_scoped_to_user(self, api_client, case_service, payment_service, case_owner, other_user, draft_case):
        # Create a case for another user
        p = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_other_list_001",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=other_user, reason="complete")
        other_case = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        assert other_case is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/cases/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(draft_case.id) in ids
        assert str(other_case.id) not in ids

    def test_list_cases_user_id_param_forbidden_for_non_staff(self, api_client, case_owner, other_user):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/cases/?user_id={other_user.id}")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_cases_invalid_pagination_returns_400(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/cases/?page=0")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_cases_staff_can_see_all(self, api_client, case_service, payment_service, admin_user, case_owner, other_user):
        p1 = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_staff_001",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(p1.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(p1.id), status="completed", changed_by=case_owner, reason="complete")
        p2 = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_staff_002",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p2.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p2.id), status="completed", changed_by=other_user, reason="complete")
        c1 = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        c2 = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{BASE}/cases/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]["items"]}
        assert str(c1.id) in ids
        assert str(c2.id) in ids

    def test_create_case_staff_can_create_for_other_user_with_payment(self, api_client, case_service, payment_service, admin_user, other_user):
        # Prepay target user (payment requirement is evaluated against requested user_id)
        p = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_staff_create_other_001",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=other_user, reason="complete")

        api_client.force_authenticate(user=admin_user)
        payload = {"user_id": str(other_user.id), "jurisdiction": "US", "status": "draft"}
        resp = api_client.post(f"{BASE}/cases/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert str(resp.data["data"]["user"]) == str(other_user.id)

    def test_get_case_detail_owner_success(self, api_client, case_owner, draft_case):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/cases/{draft_case.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(draft_case.id)

    def test_get_case_detail_other_user_forbidden(self, api_client, case_service, payment_service, case_owner, other_user):
        p = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_other_detail_001",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=other_user, reason="complete")
        other_case = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/cases/{other_case.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_case_requires_payment(self, api_client, case_owner, case_without_completed_payment):
        api_client.force_authenticate(user=case_owner)
        payload = {"jurisdiction": "CA", "version": case_without_completed_payment.version, "reason": "test"}
        resp = api_client.patch(f"{BASE}/cases/{case_without_completed_payment.id}/update/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "payment" in (resp.data.get("message") or "").lower()

    def test_update_case_paid_success(self, api_client, case_service, case_owner, paid_case):
        case, _payment = paid_case
        api_client.force_authenticate(user=case_owner)
        current = case_service.get_by_id(str(case.id))
        payload = {"jurisdiction": "CA", "version": current.version, "reason": "test"}
        resp = api_client.patch(f"{BASE}/cases/{case.id}/update/", payload, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["jurisdiction"] == "CA"

    def test_update_case_conflict_returns_409(self, api_client, case_service, case_owner, paid_case):
        case, _payment = paid_case
        api_client.force_authenticate(user=case_owner)
        current = case_service.get_by_id(str(case.id))

        payload = {"jurisdiction": "CA", "version": current.version, "reason": "first"}
        resp1 = api_client.patch(f"{BASE}/cases/{case.id}/update/", payload, format="json")
        assert resp1.status_code == status.HTTP_200_OK

        # Stale version
        payload2 = {"jurisdiction": "AU", "version": current.version, "reason": "stale"}
        resp2 = api_client.patch(f"{BASE}/cases/{case.id}/update/", payload2, format="json")
        assert resp2.status_code == status.HTTP_409_CONFLICT

    def test_delete_case_requires_payment(self, api_client, case_owner, case_without_completed_payment):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.delete(f"{BASE}/cases/{case_without_completed_payment.id}/delete/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "payment" in (resp.data.get("message") or "").lower()

    def test_delete_case_other_user_forbidden(self, api_client, case_service, payment_service, case_owner, other_user):
        p = payment_service.create_payment(
            user_id=str(other_user.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_other_delete_001",
            changed_by=other_user,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=other_user, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=other_user, reason="complete")
        other_case = case_service.create_case(user_id=str(other_user.id), jurisdiction="US", status="draft")
        api_client.force_authenticate(user=case_owner)
        resp = api_client.delete(f"{BASE}/cases/{other_case.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

