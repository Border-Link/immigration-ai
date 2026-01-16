import uuid

import pytest

from human_reviews.selectors.decision_override_selector import DecisionOverrideSelector


@pytest.mark.django_db
class TestDecisionOverrideService:
    def test_create_decision_override_returns_none_when_case_missing(self, decision_override_service, eligibility_result):
        created = decision_override_service.create_decision_override(
            case_id=str(uuid.uuid4()),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="test",
        )
        assert created is None

    def test_create_decision_override_requires_completed_payment(self, decision_override_service, case_without_completed_payment):
        # Payment validation fails before the service needs to fetch/validate the eligibility result,
        # so we deliberately avoid creating an eligibility_result fixture here.
        created = decision_override_service.create_decision_override(
            case_id=str(case_without_completed_payment.id),
            original_result_id=str(uuid.uuid4()),
            overridden_outcome="eligible",
            reason="test",
        )
        assert created is None

    def test_create_decision_override_returns_none_when_result_not_for_case(self, decision_override_service, paid_case, eligibility_result, case_service, payment_service, user_service):
        # Create another paid case so the eligibility_result belongs to a different case
        case, _payment = paid_case
        other_owner = user_service.create_user(email=f"owner-hr-{uuid.uuid4().hex[:6]}@example.com", password="testpass123")
        user_service.activate_user(other_owner)

        # Pre-case payment required for case creation
        from decimal import Decimal

        pre = payment_service.create_payment(
            user_id=str(other_owner.id),
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id=f"txn_hr_other_{uuid.uuid4().hex[:6]}",
            changed_by=other_owner,
        )
        assert pre is not None
        pre = payment_service.update_payment(payment_id=str(pre.id), status="processing", changed_by=other_owner, reason="processing")
        assert pre is not None
        pre = payment_service.update_payment(payment_id=str(pre.id), status="completed", changed_by=other_owner, reason="completed")
        assert pre is not None

        other_case = case_service.create_case(user_id=str(other_owner.id), jurisdiction="US", status="draft")
        assert other_case is not None

        created = decision_override_service.create_decision_override(
            case_id=str(other_case.id),  # case does NOT match original eligibility result's case
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="test",
        )
        assert created is None

    def test_create_decision_override_returns_none_on_invalid_outcome(self, decision_override_service, paid_case, eligibility_result):
        case, _payment = paid_case
        created = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="not-a-valid-outcome",
            reason="test",
        )
        assert created is None

    def test_create_decision_override_success_creates_override_and_completes_review(self, decision_override_service, paid_case, eligibility_result, review_service, reviewer_user):
        case, _payment = paid_case

        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None
        assert review.status == "in_progress"

        created = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="override reason",
            reviewer_id=str(reviewer_user.id),
            review_id=str(review.id),
        )
        assert created is not None
        assert str(created.case_id) == str(case.id)
        assert str(created.original_result_id) == str(eligibility_result.id)
        assert created.overridden_outcome == "eligible"

        # Ensure it's retrievable via selector paths used by the service
        latest = decision_override_service.get_latest_by_original_result(str(eligibility_result.id))
        assert latest is not None
        assert str(latest.id) == str(created.id)

        # Service attempts to complete the review when review_id is provided
        refreshed = review_service.get_by_id(str(review.id))
        assert refreshed is not None
        assert refreshed.status == "completed"

    def test_get_by_id_returns_none_when_missing(self, decision_override_service):
        found = decision_override_service.get_by_id(str(uuid.uuid4()))
        assert found is None

    def test_get_latest_returns_none_when_no_override(self, decision_override_service, eligibility_result_service, paid_case, visa_type, rule_version):
        case, _payment = paid_case
        # Create another eligibility result with no overrides
        result = eligibility_result_service.create_eligibility_result(
            case_id=str(case.id),
            visa_type_id=str(visa_type.id),
            rule_version_id=str(rule_version.id),
            outcome="eligible",
            confidence=0.5,
            reasoning_summary="another",
            missing_facts={},
        )
        assert result is not None

        latest = decision_override_service.get_latest_by_original_result(str(result.id))
        assert latest is None

    def test_delete_decision_override_success_and_missing(self, decision_override_service, paid_case, eligibility_result, reviewer_user):
        case, _payment = paid_case
        created = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="override reason",
            reviewer_id=str(reviewer_user.id),
        )
        assert created is not None

        ok = decision_override_service.delete_decision_override(str(created.id))
        assert ok is True
        assert DecisionOverrideSelector.get_all().filter(id=created.id).exists() is False

        missing_ok = decision_override_service.delete_decision_override(str(uuid.uuid4()))
        assert missing_ok is False

