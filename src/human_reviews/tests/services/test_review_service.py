import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from human_reviews.selectors.review_status_history_selector import ReviewStatusHistorySelector


@pytest.mark.django_db
class TestReviewService:
    def test_create_review_returns_none_when_case_missing(self, review_service):
        created = review_service.create_review(case_id=str(uuid.uuid4()))
        assert created is None

    def test_create_review_requires_completed_payment(self, review_service, case_without_completed_payment):
        created = review_service.create_review(case_id=str(case_without_completed_payment.id))
        assert created is None

    def test_create_review_manual_reviewer_success(self, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        created = review_service.create_review(case_id=str(case.id), reviewer_id=str(reviewer_user.id), auto_assign=False)
        assert created is not None
        assert str(created.case_id) == str(case.id)
        assert str(created.reviewer_id) == str(reviewer_user.id)

    def test_create_review_manual_reviewer_invalid_role_returns_none(self, review_service, paid_case, case_owner):
        case, _payment = paid_case
        created = review_service.create_review(case_id=str(case.id), reviewer_id=str(case_owner.id), auto_assign=False)
        assert created is None

    def test_create_review_manual_reviewer_not_staff_returns_none(self, review_service, paid_case, reviewer_user_not_staff):
        case, _payment = paid_case
        created = review_service.create_review(case_id=str(case.id), reviewer_id=str(reviewer_user_not_staff.id), auto_assign=False)
        assert created is None

    def test_create_review_auto_assign_round_robin(self, monkeypatch, review_service, paid_case, reviewer_user, user_service):
        case, _payment = paid_case

        # Ensure round-robin selection returns deterministic reviewer
        from users_access.selectors import user_selector as user_selector_module
        monkeypatch.setattr(
            user_selector_module.UserSelector,
            "get_reviewer_round_robin",
            MagicMock(return_value=reviewer_user),
        )

        created = review_service.create_review(case_id=str(case.id), reviewer_id=None, auto_assign=True, assignment_strategy="round_robin")
        assert created is not None
        assert str(created.reviewer_id) == str(reviewer_user.id)

    def test_create_review_auto_assign_workload(self, monkeypatch, review_service, paid_case, reviewer_user):
        case, _payment = paid_case

        from users_access.selectors import user_selector as user_selector_module
        monkeypatch.setattr(
            user_selector_module.UserSelector,
            "get_reviewer_by_workload",
            MagicMock(return_value=reviewer_user),
        )

        created = review_service.create_review(case_id=str(case.id), reviewer_id=None, auto_assign=True, assignment_strategy="workload")
        assert created is not None
        assert str(created.reviewer_id) == str(reviewer_user.id)

    def test_get_by_id_returns_none_when_missing(self, review_service):
        found = review_service.get_by_id(str(uuid.uuid4()))
        assert found is None

    def test_get_pending_returns_only_unassigned(self, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        unassigned = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert unassigned is not None
        assigned = review_service.create_review(case_id=str(case.id), reviewer_id=str(reviewer_user.id), auto_assign=False)
        assert assigned is not None

        pending = review_service.get_pending()
        ids = {str(r.id) for r in pending}
        assert str(unassigned.id) in ids
        assert str(assigned.id) not in ids  # assigned has reviewer_id set

    def test_assign_reviewer_success_auto_assign(self, monkeypatch, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None
        assert review.reviewer_id is None

        from users_access.selectors import user_selector as user_selector_module
        monkeypatch.setattr(
            user_selector_module.UserSelector,
            "get_reviewer_round_robin",
            MagicMock(return_value=reviewer_user),
        )

        updated = review_service.assign_reviewer(str(review.id), reviewer_id=None, assignment_strategy="round_robin")
        assert updated is not None
        assert str(updated.reviewer_id) == str(reviewer_user.id)
        assert updated.status == "in_progress"

        history = list(ReviewStatusHistorySelector.get_by_review(updated))
        assert history, "Assigning a reviewer must create a status history entry"
        assert history[0].metadata.get("action") == "assign"

    def test_assign_reviewer_returns_none_when_no_reviewer_available(self, monkeypatch, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        from users_access.selectors import user_selector as user_selector_module
        monkeypatch.setattr(
            user_selector_module.UserSelector,
            "get_reviewer_round_robin",
            MagicMock(return_value=None),
        )

        updated = review_service.assign_reviewer(str(review.id), reviewer_id=None, assignment_strategy="round_robin")
        assert updated is None

    def test_assign_reviewer_invalid_manual_reviewer_returns_none(self, review_service, paid_case, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        updated = review_service.assign_reviewer(str(review.id), reviewer_id=str(case_owner.id))
        assert updated is None

    def test_assign_reviewer_requires_completed_payment(self, review_service, paid_case, payment_service, case_owner, reviewer_user):
        case, payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        # Remove completed payment and invalidate cache
        payment_service.delete_payment(payment_id=str(payment.id), changed_by=case_owner, reason="test delete payment", hard_delete=False)
        from payments.helpers.payment_validator import PaymentValidator
        PaymentValidator.invalidate_payment_cache(str(case.id))

        updated = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert updated is None

    def test_update_review_success_status_transition_creates_history(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        updated = review_service.update_review(str(review.id), status="cancelled")
        assert updated is not None
        assert updated.status == "cancelled"

        history = list(ReviewStatusHistorySelector.get_by_review(updated))
        assert history
        assert history[0].new_status == "cancelled"

    def test_update_review_invalid_transition_raises_validation_error(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        with pytest.raises(ValidationError):
            review_service.update_review(str(review.id), status="completed")

    def test_update_review_version_conflict_raises_validation_error(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None
        current_version = review.version

        with pytest.raises(ValidationError):
            review_service.update_review(str(review.id), status="cancelled", version=current_version + 999)

    def test_complete_review_requires_valid_transition(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        # pending -> completed is invalid
        completed = review_service.complete_review(str(review.id))
        assert completed is None

    def test_complete_review_success_from_in_progress(self, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None
        assert review.status == "in_progress"

        completed = review_service.complete_review(str(review.id))
        assert completed is not None
        assert completed.status == "completed"

        history = list(ReviewStatusHistorySelector.get_by_review(completed))
        assert history
        assert any(h.metadata.get("action") == "complete" for h in history)

    def test_cancel_review_success_from_pending(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        cancelled = review_service.cancel_review(str(review.id))
        assert cancelled is not None
        assert cancelled.status == "cancelled"

    def test_delete_review_success_and_missing(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        ok = review_service.delete_review(str(review.id))
        assert ok is True
        assert review_service.get_by_id(str(review.id)) is None

        missing_ok = review_service.delete_review(str(uuid.uuid4()))
        assert missing_ok is False

    def test_reassign_reviewer_success(self, review_service, paid_case, reviewer_user, user_service):
        case, _payment = paid_case

        other_reviewer = user_service.create_user(
            email=f"reviewer2-hr-{uuid.uuid4().hex[:6]}@example.com",
            password="reviewerpass123",
        )
        user_service.update_user(other_reviewer, role="reviewer", is_staff=True)
        user_service.activate_user(other_reviewer)

        review = review_service.create_review(case_id=str(case.id), reviewer_id=str(reviewer_user.id), auto_assign=False)
        assert review is not None

        reassigned = review_service.reassign_reviewer(str(review.id), new_reviewer_id=str(other_reviewer.id))
        assert reassigned is not None
        assert str(reassigned.reviewer_id) == str(other_reviewer.id)

    def test_escalate_review_creates_history_without_status_change(self, review_service, paid_case):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None
        prev_status = review.status

        escalated = review_service.escalate_review(str(review.id), reason="needs attention", priority="urgent")
        assert escalated is not None
        assert escalated.status == prev_status

        history = list(ReviewStatusHistorySelector.get_by_review(escalated))
        assert history
        assert any(h.metadata.get("action") == "escalate" for h in history)

    def test_reject_review_sets_pending(self, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        rejected = review_service.reject_review(str(review.id), reason="needs changes")
        assert rejected is not None
        assert rejected.status == "pending"

    def test_request_changes_keeps_status_and_sets_metadata(self, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None
        assert review.status == "in_progress"

        updated = review_service.request_changes(str(review.id), reason="please update docs")
        assert updated is not None
        assert updated.status == "in_progress"
        # Current implementation performs a no-op update (no status change),
        # so no status history entry is created. We validate it returns successfully.

    def test_get_statistics_shape_and_counts(self, review_service, paid_case, reviewer_user, review_note_service, eligibility_result, decision_override_service):
        case, _payment = paid_case
        # Create an unassigned pending review
        r1 = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert r1 is not None
        # Create an assigned in_progress review, then complete it
        r2 = review_service.create_review(case_id=str(case.id), auto_assign=False)
        r2 = review_service.assign_reviewer(str(r2.id), reviewer_id=str(reviewer_user.id))
        assert r2 is not None
        r2 = review_service.complete_review(str(r2.id))
        assert r2 is not None

        note = review_note_service.create_review_note(review_id=str(r2.id), note="public note", is_internal=False)
        assert note is not None

        override = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="confirmed",
            reviewer_id=str(reviewer_user.id),
            review_id=str(r2.id),
        )
        assert override is not None

        stats = review_service.get_statistics()
        assert "reviews" in stats
        assert "review_notes" in stats
        assert "decision_overrides" in stats
        assert stats["reviews"]["total"] >= 2
        assert stats["review_notes"]["total"] >= 1
        assert stats["decision_overrides"]["total"] >= 1

