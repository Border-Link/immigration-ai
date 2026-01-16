import uuid

import pytest


@pytest.mark.django_db
class TestReviewNoteService:
    def test_create_review_note_returns_none_when_review_missing(self, review_note_service):
        created = review_note_service.create_review_note(review_id=str(uuid.uuid4()), note="hello", is_internal=False)
        assert created is None

    def test_create_review_note_requires_completed_payment(self, review_note_service, review_service, paid_case, payment_service, case_owner, reviewer_user):
        case, payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        # Remove completed payment and invalidate cache
        payment_service.delete_payment(payment_id=str(payment.id), changed_by=case_owner, reason="test delete payment", hard_delete=False)
        from payments.helpers.payment_validator import PaymentValidator

        PaymentValidator.invalidate_payment_cache(str(case.id))

        created = review_note_service.create_review_note(review_id=str(review.id), note="hello", is_internal=False)
        assert created is None

    def test_create_and_read_public_notes(self, review_note_service, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        n1 = review_note_service.create_review_note(review_id=str(review.id), note="public note", is_internal=False)
        n2 = review_note_service.create_review_note(review_id=str(review.id), note="internal note", is_internal=True)
        assert n1 is not None
        assert n2 is not None

        public = list(review_note_service.get_public_by_review(str(review.id)))
        assert any(str(n.id) == str(n1.id) for n in public)
        assert all(n.is_internal is False for n in public)

    def test_get_by_id_returns_none_when_missing(self, review_note_service):
        found = review_note_service.get_by_id(str(uuid.uuid4()))
        assert found is None

    def test_update_review_note_success(self, review_note_service, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        note = review_note_service.create_review_note(review_id=str(review.id), note="before", is_internal=False)
        assert note is not None

        updated = review_note_service.update_review_note(str(note.id), note="after", is_internal=True)
        assert updated is not None
        assert updated.note == "after"
        assert updated.is_internal is True

    def test_delete_review_note_success_and_missing(self, review_note_service, review_service, paid_case, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        note = review_note_service.create_review_note(review_id=str(review.id), note="to delete", is_internal=False)
        assert note is not None

        ok = review_note_service.delete_review_note(str(note.id))
        assert ok is True
        assert review_note_service.get_by_id(str(note.id)) is None

        missing_ok = review_note_service.delete_review_note(str(uuid.uuid4()))
        assert missing_ok is False

