"""
Tests for CaseService.

All tests use services as the entrypoint (no direct model usage in tests).
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestCaseService:
    def test_create_case_without_payment_returns_none(self, case_service, case_owner):
        case = case_service.create_case(
            user_id=str(case_owner.id),
            jurisdiction="US",
            status="draft",
        )
        assert case is None

    def test_create_case_success_with_prepayment(self, case_service, payment_service, case_owner):
        payment = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_case_create_001",
            changed_by=case_owner,
        )
        assert payment is not None
        payment_service.update_payment(
            payment_id=str(payment.id),
            status="processing",
            changed_by=case_owner,
            reason="processing",
        )
        payment_service.update_payment(
            payment_id=str(payment.id),
            status="completed",
            changed_by=case_owner,
            reason="complete",
        )
        case = case_service.create_case(
            user_id=str(case_owner.id),
            jurisdiction="US",
            status="draft",
        )
        assert case is not None
        assert str(case.user.id) == str(case_owner.id)
        assert case.jurisdiction == "US"
        assert case.status == "draft"
        assert case.version == 1

    def test_create_case_invalid_user_returns_none(self, case_service):
        case = case_service.create_case(
            user_id="00000000-0000-0000-0000-000000000000",
            jurisdiction="US",
            status="draft",
        )
        assert case is None

    def test_get_by_id_invalid_format_returns_none(self, case_service):
        assert case_service.get_by_id("not-a-uuid") is None

    def test_get_by_id_not_found_returns_none(self, case_service):
        assert case_service.get_by_id("00000000-0000-0000-0000-000000000000") is None

    def test_get_all_includes_created_case(self, case_service, draft_case):
        cases = case_service.get_all()
        assert cases is not None
        assert cases.filter(id=draft_case.id).exists()

    def test_get_by_user_filters_correctly(self, case_service, user_service, case_owner):
        other = user_service.create_user(email="case-other@example.com", password="testpass123")
        user_service.activate_user(other)
        from payments.services.payment_service import PaymentService

        # Prepay both users
        p1 = PaymentService.create_payment(
            user_id=str(case_owner.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_filter_001",
            changed_by=case_owner,
        )
        PaymentService.update_payment(payment_id=str(p1.id), status="processing", changed_by=case_owner, reason="processing")
        PaymentService.update_payment(payment_id=str(p1.id), status="completed", changed_by=case_owner, reason="complete")
        p2 = PaymentService.create_payment(
            user_id=str(other.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_filter_002",
            changed_by=other,
        )
        PaymentService.update_payment(payment_id=str(p2.id), status="processing", changed_by=other, reason="processing")
        PaymentService.update_payment(payment_id=str(p2.id), status="completed", changed_by=other, reason="complete")

        c1 = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        c2 = case_service.create_case(user_id=str(other.id), jurisdiction="US", status="draft")
        by_owner = case_service.get_by_user(str(case_owner.id))
        assert by_owner.filter(id=c1.id).exists()
        assert not by_owner.filter(id=c2.id).exists()

    def test_update_case_without_payment_is_blocked(self, case_service, case_without_completed_payment):
        updated, error, http_status = case_service.update_case(
            case_id=str(case_without_completed_payment.id),
            version=case_without_completed_payment.version,
            jurisdiction="CA",
        )
        assert updated is None
        assert http_status == 400
        assert error and "completed payment" in error.lower()

    def test_update_case_with_payment_succeeds(self, case_service, paid_case):
        case, _payment = paid_case
        current = case_service.get_by_id(str(case.id))
        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            jurisdiction="CA",
            reason="update jurisdiction",
        )
        assert error is None
        assert http_status is None
        assert updated is not None
        assert updated.jurisdiction == "CA"
        assert updated.version == current.version + 1

    def test_status_transition_to_evaluated_requires_fact(self, case_service, paid_case):
        case, _payment = paid_case
        current = case_service.get_by_id(str(case.id))
        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            status="evaluated",
            reason="attempt evaluate",
        )
        assert updated is None
        assert http_status == 400
        assert error and "at least one fact" in error.lower()

    def test_status_transition_to_evaluated_with_fact_creates_history(
        self, case_service, case_status_history_service, paid_case_with_fact, case_owner
    ):
        case, _fact = paid_case_with_fact
        current = case_service.get_by_id(str(case.id))

        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            updated_by_id=str(case_owner.id),
            version=current.version,
            status="evaluated",
            reason="evaluation completed",
        )
        assert error is None
        assert http_status is None
        assert updated is not None
        assert updated.status == "evaluated"

        history = case_status_history_service.get_by_case_id(str(case.id))
        assert history.count() >= 1
        latest = history.first()
        assert latest.previous_status == "draft"
        assert latest.new_status == "evaluated"
        assert latest.reason == "evaluation completed"

    def test_update_case_optimistic_locking_conflict(self, case_service, paid_case):
        case, _payment = paid_case
        current = case_service.get_by_id(str(case.id))

        # First update (valid)
        updated1, error1, http_status1 = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            jurisdiction="CA",
            reason="first update",
        )
        assert updated1 is not None
        assert error1 is None
        assert http_status1 is None

        # Second update with stale version -> conflict
        updated2, error2, http_status2 = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            jurisdiction="AU",
            reason="stale update",
        )
        assert updated2 is None
        assert http_status2 == 409
        assert error2 and "modified by another user" in error2.lower()

    def test_invalid_status_transition_returns_400(self, case_service, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        current = case_service.get_by_id(str(case.id))

        # Move to evaluated first (valid)
        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            status="evaluated",
            reason="evaluate",
        )
        assert updated is not None

        # Invalid: evaluated -> draft
        updated2, error2, http_status2 = case_service.update_case(
            case_id=str(case.id),
            version=updated.version,
            status="draft",
            reason="invalid transition",
        )
        assert updated2 is None
        assert http_status2 == 400
        assert error2 and "invalid transition" in error2.lower()

    def test_delete_case_requires_payment(self, case_service, case_without_completed_payment):
        assert case_service.delete_case(str(case_without_completed_payment.id)) is False

    def test_delete_case_with_payment_soft_deletes_and_can_restore(self, case_service, paid_case, case_owner):
        case, _payment = paid_case
        deleted = case_service.delete_case(str(case.id), deleted_by_id=str(case_owner.id), hard_delete=False)
        assert deleted is True

        # Soft-deleted cases should not be retrievable via service selector (excludes deleted)
        assert case_service.get_by_id(str(case.id)) is None

        restored = case_service.restore_case(str(case.id), restored_by_id=str(case_owner.id))
        assert restored is not None
        assert restored.is_deleted is False

    def test_restore_case_non_deleted_is_noop(self, case_service, paid_case, case_owner):
        case, _payment = paid_case
        restored = case_service.restore_case(str(case.id), restored_by_id=str(case_owner.id))
        assert restored is not None
        assert str(restored.id) == str(case.id)

    def test_get_by_filters(self, case_service, draft_case):
        results = case_service.get_by_filters(jurisdiction="US", status="draft")
        assert results.filter(id=draft_case.id).exists()

    def test_create_case_attaches_most_recent_unassigned_completed_payment(self, case_service, payment_service, case_owner):
        p1 = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_attach_001",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(p1.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(p1.id), status="completed", changed_by=case_owner, reason="complete")

        p2 = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_attach_002",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(p2.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(p2.id), status="completed", changed_by=case_owner, reason="complete")

        case = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        assert case is not None

        refreshed_p2 = payment_service.get_by_id(str(p2.id))
        refreshed_p1 = payment_service.get_by_id(str(p1.id))
        assert str(refreshed_p2.case_id) == str(case.id)
        assert refreshed_p1.case_id is None

    def test_create_case_consumes_payment_entitlement(self, case_service, payment_service, case_owner):
        p = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_once_001",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=case_owner, reason="complete")

        created = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        assert created is not None

        # No additional unassigned completed payment -> cannot create another case.
        created2 = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        assert created2 is None

    def test_case_status_transition_validator_module_importable(self):
        # Coverage for helper modules (sanity import)
        from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator

        assert CaseStatusTransitionValidator.get_valid_transitions("draft") == ["evaluated", "closed"]

    def test_update_case_not_found_returns_404(self, case_service):
        updated, error, http_status = case_service.update_case(
            case_id="00000000-0000-0000-0000-000000000000",
            version=1,
            jurisdiction="CA",
            reason="test",
        )
        assert updated is None
        assert http_status == 404
        assert error and "not found" in error.lower()

    def test_update_case_unexpected_exception_returns_500(self, monkeypatch, case_service, paid_case):
        """
        Production-standard failure-path: unexpected errors are translated to a safe 500 tuple.
        """
        case, _payment = paid_case

        from immigration_cases.repositories.case_repository import CaseRepository

        def _boom(*args, **kwargs):
            raise Exception("boom")

        monkeypatch.setattr(CaseRepository, "update_case", _boom)

        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            version=case.version,
            jurisdiction="CA",
            reason="test",
        )
        assert updated is None
        assert http_status == 500
        assert error and "boom" in error.lower()

