from decimal import Decimal
from uuid import uuid4

import pytest


@pytest.mark.django_db
class TestPaymentServiceCore:
    def test_create_payment_requires_exactly_one_of_case_or_user(self, payment_service):
        p1 = payment_service.create_payment(amount=Decimal("10.00"), currency="USD", payment_provider="stripe")
        assert p1 is None

        p2 = payment_service.create_payment(
            amount=Decimal("10.00"),
            case_id=str(uuid4()),
            user_id=str(uuid4()),
            currency="USD",
            payment_provider="stripe",
        )
        assert p2 is None

    def test_create_payment_invalid_user_returns_none(self, payment_service):
        p = payment_service.create_payment(
            user_id=str(uuid4()),
            amount=Decimal("10.00"),
            currency="USD",
            payment_provider="stripe",
            plan="basic",
        )
        assert p is None

    def test_create_payment_success_prepayment(self, payment_service, payment_owner):
        p = payment_service.create_payment(
            user_id=str(payment_owner.id),
            amount=Decimal("10.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_001",
            plan="basic",
            changed_by=payment_owner,
        )
        assert p is not None
        assert str(p.user_id) == str(payment_owner.id)
        assert p.case_id is None
        assert p.status == "pending"
        assert p.currency == "USD"
        assert p.payment_provider == "stripe"

    def test_create_payment_unsupported_currency_defaults_to_usd(self, payment_service, payment_owner):
        p = payment_service.create_payment(
            user_id=str(payment_owner.id),
            amount=Decimal("10.00"),
            currency="XXX",
            status="pending",
            payment_provider="stripe",
            plan="basic",
            changed_by=payment_owner,
        )
        assert p is not None
        assert p.currency == "USD"

    def test_get_by_id_not_found_returns_none(self, payment_service):
        assert payment_service.get_by_id(str(uuid4())) is None

    def test_update_payment_status_valid_transition(self, payment_service, pre_case_payment_pending, payment_owner):
        updated = payment_service.update_payment(
            payment_id=str(pre_case_payment_pending.id),
            status="processing",
            changed_by=payment_owner,
            reason="start processing",
        )
        assert updated is not None
        assert updated.status == "processing"
        assert updated.version >= 2

    def test_update_payment_status_invalid_transition_returns_none(self, payment_service, pre_case_payment_pending, payment_owner):
        # pending -> refunded is invalid per state machine
        updated = payment_service.update_payment(
            payment_id=str(pre_case_payment_pending.id),
            status="refunded",
            changed_by=payment_owner,
            reason="invalid transition",
        )
        assert updated is None

    def test_update_payment_version_conflict_returns_none(self, payment_service, pre_case_payment_pending, payment_owner):
        # initial version is 1; use wrong expected version
        updated = payment_service.update_payment(
            payment_id=str(pre_case_payment_pending.id),
            version=999,
            status="processing",
            changed_by=payment_owner,
            reason="version conflict",
        )
        assert updated is None

    def test_delete_payment_soft_and_restore(self, payment_service, pre_case_payment_pending, payment_owner):
        ok = payment_service.delete_payment(
            payment_id=str(pre_case_payment_pending.id),
            changed_by=payment_owner,
            reason="test delete",
            hard_delete=False,
        )
        assert ok is True

        deleted = payment_service.get_by_id(str(pre_case_payment_pending.id))
        assert deleted is None  # selector filters deleted

        restored = payment_service.restore_payment(str(pre_case_payment_pending.id), restored_by=payment_owner)
        assert restored is not None
        assert restored.is_deleted is False

    def test_delete_payment_not_found_returns_false(self, payment_service):
        ok = payment_service.delete_payment(payment_id=str(uuid4()), changed_by=None, reason="missing")
        assert ok is False

