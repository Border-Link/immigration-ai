from decimal import Decimal

import pytest
from rest_framework import status

from payments.services.pricing_service import PricingService


BASE = "/api/v1/payments"


@pytest.mark.django_db
class TestPlanAndAddonPurchaseViews:
    def test_plan_purchase_requires_auth(self, api_client):
        resp = api_client.post(f"{BASE}/plans/case-fee/", {"plan": "basic", "payment_provider": "stripe"}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_plan_purchase_creates_pre_case_payment_with_server_amount(self, api_client, payment_owner):
        item = PricingService.create_item(
            kind="plan",
            code="basic",
            name="Basic Plan",
            description="",
            is_active=True,
            includes_ai_calls=False,
            includes_human_review=False,
        )
        assert item is not None
        price = PricingService.upsert_price(str(item.id), currency="USD", amount=Decimal("100.00"))
        assert price is not None

        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(
            f"{BASE}/plans/case-fee/",
            {"plan": "basic", "payment_provider": "stripe", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.data["data"]
        assert data["purpose"] == "case_fee"
        assert data["plan"] == "basic"
        assert Decimal(str(data["amount"])) == Decimal("100.00")

    def test_plan_purchase_uses_admin_configured_price_when_present(self, api_client, payment_owner):
        # Admin config: override basic USD price
        item = PricingService.create_item(
            kind="plan",
            code="basic",
            name="Basic Plan",
            description="",
            is_active=True,
            includes_ai_calls=False,
            includes_human_review=False,
        )
        assert item is not None
        assert PricingService.upsert_price(str(item.id), currency="USD", amount=Decimal("123.45")) is not None

        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(
            f"{BASE}/plans/case-fee/",
            {"plan": "basic", "payment_provider": "stripe", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.data["data"]
        assert Decimal(str(data["amount"])) == Decimal("123.45")

    def test_plan_purchase_returns_400_when_currency_price_missing(self, api_client, payment_owner):
        item = PricingService.create_item(
            kind="plan",
            code="special",
            name="Special Plan",
            description="",
            is_active=True,
            includes_ai_calls=True,
            includes_human_review=False,
        )
        assert item is not None
        # No GBP price configured
        assert PricingService.upsert_price(str(item.id), currency="USD", amount=Decimal("200.00")) is not None

        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(
            f"{BASE}/plans/case-fee/",
            {"plan": "special", "payment_provider": "stripe", "currency": "GBP"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def _create_case_with_plan(self, case_service, payment_service, owner, plan: str):
        # Create a completed pre-case payment with the requested plan
        p = payment_service.create_payment(
            user_id=str(owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id=f"txn_case_{plan}",
            plan=plan,
            changed_by=owner,
        )
        p = payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=owner, reason="processing")
        p = payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=owner, reason="completed")
        case = case_service.create_case(user_id=str(owner.id), jurisdiction="US", status="draft")
        assert case is not None
        return case

    def test_reviewer_addon_purchase_requires_case_owner(self, api_client, case_service, payment_service, payment_owner, other_user):
        case = self._create_case_with_plan(case_service, payment_service, payment_owner, plan="basic")
        api_client.force_authenticate(user=other_user)
        resp = api_client.post(
            f"{BASE}/cases/{case.id}/reviewer-addon/",
            {"payment_provider": "stripe", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_reviewer_addon_purchase_blocks_when_big_plan(self, api_client, case_service, payment_service, payment_owner):
        case = self._create_case_with_plan(case_service, payment_service, payment_owner, plan="big")
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(
            f"{BASE}/cases/{case.id}/reviewer-addon/",
            {"payment_provider": "stripe", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reviewer_addon_purchase_success_creates_case_attached_payment(self, api_client, case_service, payment_service, payment_owner):
        addon = PricingService.create_item(
            kind="addon",
            code="reviewer_addon",
            name="Reviewer Add-on",
            description="",
            is_active=True,
            includes_ai_calls=False,
            includes_human_review=True,
        )
        assert addon is not None
        assert PricingService.upsert_price(str(addon.id), currency="USD", amount=Decimal("50.00")) is not None

        case = self._create_case_with_plan(case_service, payment_service, payment_owner, plan="basic")
        api_client.force_authenticate(user=payment_owner)
        resp = api_client.post(
            f"{BASE}/cases/{case.id}/reviewer-addon/",
            {"payment_provider": "stripe", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.data["data"]
        assert data["case_id"] == str(case.id)
        assert data["purpose"] == "reviewer_addon"
        assert data["plan"] is None
        assert Decimal(str(data["amount"])) == Decimal("50.00")

    def test_entitlements_endpoint_reflects_plan_and_addons(self, api_client, case_service, payment_service, payment_owner):
        special = PricingService.create_item(
            kind="plan",
            code="special",
            name="Special Plan",
            description="",
            is_active=True,
            includes_ai_calls=True,
            includes_human_review=False,
        )
        assert special is not None

        case = self._create_case_with_plan(case_service, payment_service, payment_owner, plan="special")
        api_client.force_authenticate(user=payment_owner)

        resp = api_client.get(f"{BASE}/cases/{case.id}/entitlements/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        assert data["has_case_fee_payment"] is True
        assert data["plan"] == "special"
        assert data["entitlements"]["ai_calls"] is True
        # Human review not included on special unless add-on exists
        assert data["entitlements"]["human_review"] is False

    def test_ai_calls_addon_purchase_allows_basic_plan_to_use_ai_calls_entitlement(self, api_client, case_service, payment_service, payment_owner):
        ai_calls_addon = PricingService.create_item(
            kind="addon",
            code="ai_calls_addon",
            name="AI Calls Add-on",
            description="",
            is_active=True,
            includes_ai_calls=True,
            includes_human_review=False,
        )
        assert ai_calls_addon is not None
        assert PricingService.upsert_price(str(ai_calls_addon.id), currency="USD", amount=Decimal("50.00")) is not None

        case = self._create_case_with_plan(case_service, payment_service, payment_owner, plan="basic")
        api_client.force_authenticate(user=payment_owner)

        resp = api_client.post(
            f"{BASE}/cases/{case.id}/ai-calls-addon/",
            {"payment_provider": "stripe", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        addon_payment_id = resp.data["data"]["id"]

        payment_service.update_payment(
            payment_id=str(addon_payment_id),
            status="completed",
            changed_by=payment_owner,
            reason="complete ai calls addon",
        )

        ent = api_client.get(f"{BASE}/cases/{case.id}/entitlements/")
        assert ent.status_code == status.HTTP_200_OK
        assert ent.data["data"]["entitlements"]["ai_calls"] is True
