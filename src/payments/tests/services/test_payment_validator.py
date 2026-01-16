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

