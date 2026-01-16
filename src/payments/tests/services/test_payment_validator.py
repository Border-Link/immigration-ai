from decimal import Decimal

import pytest

from payments.helpers.payment_validator import PaymentValidator


@pytest.mark.django_db
class TestPaymentValidator:
    def test_can_create_case_for_user_requires_unassigned_completed_payment(self, payment_owner):
        ok, err = PaymentValidator.can_create_case_for_user(str(payment_owner.id))
        assert ok is False
        assert err

    def test_can_create_case_for_user_true_with_unassigned_completed_payment(self, payment_service, payment_owner):
        p = payment_service.create_payment(
            user_id=str(payment_owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_can_create_001",
            plan="basic",
            changed_by=payment_owner,
        )
        assert p is not None
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=payment_owner, reason="complete")
        ok, err = PaymentValidator.can_create_case_for_user(str(payment_owner.id))
        assert ok is True
        assert err is None

    def test_has_unassigned_completed_payment_for_user(self, payment_service, payment_owner):
        ok, payment = PaymentValidator.has_unassigned_completed_payment_for_user(str(payment_owner.id))
        assert ok is False
        assert payment is None

        p = payment_service.create_payment(
            user_id=str(payment_owner.id),
            amount=Decimal("50.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_unassigned_001",
            plan="basic",
            changed_by=payment_owner,
        )
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=payment_owner, reason="complete")
        ok, payment = PaymentValidator.has_unassigned_completed_payment_for_user(str(payment_owner.id))
        assert ok is True
        assert payment is not None

    def test_validate_case_has_payment_blocks_when_deleted(self, case_without_completed_payment):
        ok, err = PaymentValidator.validate_case_has_payment(case_without_completed_payment, operation_name="test-op")
        assert ok is False
        assert "completed payment" in (err or "").lower()

    def test_validate_case_has_payment_success(self, paid_case):
        case, _payment = paid_case
        ok, err = PaymentValidator.validate_case_has_payment(case, operation_name="test-op")
        assert ok is True
        assert err is None

    def test_ensure_one_payment_per_case_blocks_duplicate_completed(self, paid_case):
        case, _payment = paid_case
        ok, err = PaymentValidator.ensure_one_payment_per_case(case)
        assert ok is False
        assert err

    def test_ai_calls_entitlement_requires_special_or_big_plan(self, paid_case, payment_service):
        case, payment = paid_case

        # Default/legacy plan is treated as basic -> should be blocked
        ok, err = PaymentValidator.validate_case_has_ai_calls_entitlement(case, operation_name="ai calls")
        assert ok is False
        assert err

        # Configure special plan entitlement and upgrade plan -> allowed
        from payments.services.pricing_service import PricingService

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
        payment_service.update_payment(
            payment_id=str(payment.id),
            plan="special",
            changed_by=payment.user,
            reason="test upgrade plan",
        )
        PaymentValidator.invalidate_payment_cache(str(case.id))

        ok2, err2 = PaymentValidator.validate_case_has_ai_calls_entitlement(case, operation_name="ai calls")
        assert ok2 is True
        assert err2 is None

    def test_human_review_entitlement_allows_big_or_addon(self, paid_case, payment_service):
        case, payment = paid_case

        ok, err = PaymentValidator.validate_case_has_human_review_entitlement(case, operation_name="human review")
        assert ok is False
        assert err

        # Purchase reviewer add-on -> allowed
        addon = payment_service.create_payment(
            case_id=str(case.id),
            amount=Decimal("50.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_addon_001",
            purpose="reviewer_addon",
            changed_by=payment.user,
        )
        assert addon is not None
        payment_service.update_payment(payment_id=str(addon.id), status="completed", changed_by=payment.user, reason="complete addon")

        ok2, err2 = PaymentValidator.validate_case_has_human_review_entitlement(case, operation_name="human review")
        assert ok2 is True
        assert err2 is None

        # Configure big plan entitlement and upgrade plan -> allowed even without add-on
        from payments.services.pricing_service import PricingService

        big = PricingService.create_item(
            kind="plan",
            code="big",
            name="Big Plan",
            description="",
            is_active=True,
            includes_ai_calls=True,
            includes_human_review=True,
        )
        assert big is not None
        payment_service.update_payment(
            payment_id=str(payment.id),
            plan="big",
            changed_by=payment.user,
            reason="test upgrade plan to big",
        )
        PaymentValidator.invalidate_payment_cache(str(case.id))
        ok3, err3 = PaymentValidator.validate_case_has_human_review_entitlement(case, operation_name="human review")
        assert ok3 is True
        assert err3 is None
