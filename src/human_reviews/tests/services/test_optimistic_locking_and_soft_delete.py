"""
Tests for optimistic locking, race conditions, conflict detection, and soft delete
in human_reviews module.
"""

import pytest
from django.core.exceptions import ValidationError
from threading import Thread, Barrier
from human_reviews.models.review import Review
from human_reviews.models.review_note import ReviewNote
from human_reviews.repositories.review_repository import ReviewRepository
from human_reviews.repositories.review_note_repository import ReviewNoteRepository
from human_reviews.repositories.decision_override_repository import DecisionOverrideRepository
from human_reviews.selectors.review_selector import ReviewSelector
from human_reviews.selectors.review_note_selector import ReviewNoteSelector
from human_reviews.selectors.decision_override_selector import DecisionOverrideSelector
from human_reviews.services.review_service import ReviewService
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.services.decision_override_service import DecisionOverrideService


@pytest.mark.django_db(transaction=True)
class TestReviewOptimisticLocking:
    """Tests for optimistic locking in Review."""

    def test_create_review_has_version_one(self, review_service, paid_case):
        """New reviews should start with version 1."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        assert review.version == 1
        assert review.is_deleted is False
        assert review.deleted_at is None

    def test_update_review_increments_version(self, review_service, paid_case):
        """Updating a review should increment its version."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        initial_version = review.version
        
        updated = ReviewRepository.update_review(
            review,
            version=initial_version,
            status="in_progress"
        )
        
        assert updated.version == initial_version + 1
        assert updated.status == "in_progress"

    def test_update_review_version_conflict_raises_error(self, review_service, paid_case):
        """Updating with wrong version should raise ValidationError."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        initial_version = review.version
        
        # First update succeeds
        ReviewRepository.update_review(
            review,
            version=initial_version,
            status="in_progress"
        )
        
        # Second update with stale version should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewRepository.update_review(
                review,
                version=initial_version,  # Stale version
                status="cancelled"
            )
        
        assert "modified by another user" in str(exc_info.value).lower()

    def test_concurrent_updates_race_condition(self, review_service, paid_case):
        """Test that concurrent updates are handled correctly."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        initial_version = review.version
        results = []
        errors = []
        barrier = Barrier(2)
        
        def update_review(thread_id):
            try:
                barrier.wait()  # Synchronize threads
                updated = ReviewRepository.update_review(
                    review,
                    version=initial_version,
                    status="in_progress" if thread_id == 1 else "cancelled"
                )
                results.append((thread_id, updated.version))
            except ValidationError as e:
                errors.append((thread_id, str(e)))
        
        # Start two threads trying to update simultaneously
        thread1 = Thread(target=update_review, args=(1,))
        thread2 = Thread(target=update_review, args=(2,))
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # One should succeed, one should fail with version conflict
        assert len(results) == 1, "Exactly one update should succeed"
        assert len(errors) == 1, "Exactly one update should fail"
        assert "modified by another user" in errors[0][1].lower()


@pytest.mark.django_db
class TestReviewSoftDelete:
    """Tests for soft delete in Review."""

    def test_soft_delete_review(self, review_service, paid_case):
        """Soft deleting a review should mark it as deleted."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        initial_version = review.version
        
        deleted = ReviewRepository.soft_delete_review(
            review,
            version=initial_version
        )
        
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None
        assert deleted.version == initial_version + 1

    def test_soft_delete_filters_from_selector(self, review_service, paid_case):
        """Soft-deleted reviews should not appear in selectors."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        
        # Review should be visible before deletion
        found = ReviewSelector.get_by_id(str(review.id))
        assert found is not None
        
        # Soft delete
        ReviewRepository.soft_delete_review(
            review,
            version=review.version
        )
        
        # Review should not be visible after deletion
        with pytest.raises(Review.DoesNotExist):
            ReviewSelector.get_by_id(str(review.id))

    def test_service_delete_uses_soft_delete(self, review_service, paid_case):
        """Service delete method should use soft delete."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        initial_version = review.version
        
        result = review_service.delete_review(
            str(review.id),
            version=initial_version
        )
        
        assert result is True
        
        # Review should be soft-deleted
        deleted_review = Review.objects.get(id=review.id)
        assert deleted_review.is_deleted is True
        
        # Should not appear in selector
        with pytest.raises(Review.DoesNotExist):
            ReviewSelector.get_by_id(str(review.id))


@pytest.mark.django_db
class TestReviewNoteOptimisticLocking:
    """Tests for optimistic locking in ReviewNote."""

    def test_create_review_note_has_version_one(self, review_note_service, review_service, paid_case):
        """New notes should start with version 1."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        
        note = review_note_service.create_review_note(
            review_id=str(review.id),
            note="Test note"
        )
        assert note.version == 1
        assert note.is_deleted is False
        assert note.deleted_at is None

    def test_update_review_note_version_conflict_raises_error(self, review_note_service, review_service, paid_case):
        """Updating with wrong version should raise ValidationError."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        
        note = review_note_service.create_review_note(
            review_id=str(review.id),
            note="Test note"
        )
        initial_version = note.version
        
        # First update succeeds
        ReviewNoteRepository.update_review_note(
            note,
            version=initial_version,
            note="Updated note"
        )
        
        # Second update with stale version should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewNoteRepository.update_review_note(
                note,
                version=initial_version,  # Stale version
                note="Second update"
            )
        
        assert "modified by another user" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestReviewNoteSoftDelete:
    """Tests for soft delete in ReviewNote."""

    def test_soft_delete_review_note(self, review_note_service, review_service, paid_case):
        """Soft deleting a note should mark it as deleted."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        
        note = review_note_service.create_review_note(
            review_id=str(review.id),
            note="Test note"
        )
        initial_version = note.version
        
        deleted = ReviewNoteRepository.soft_delete_review_note(
            note,
            version=initial_version
        )
        
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None
        assert deleted.version == initial_version + 1

    def test_soft_delete_filters_from_selector(self, review_note_service, review_service, paid_case):
        """Soft-deleted notes should not appear in selectors."""
        case, _payment = paid_case
        review = review_service.create_review(
            case_id=str(case.id),
            auto_assign=False
        )
        
        note = review_note_service.create_review_note(
            review_id=str(review.id),
            note="Test note"
        )
        
        # Note should be visible before deletion
        found = ReviewNoteSelector.get_by_id(str(note.id))
        assert found is not None
        
        # Soft delete
        ReviewNoteRepository.soft_delete_review_note(
            note,
            version=note.version
        )
        
        # Note should not be visible after deletion
        with pytest.raises(ReviewNote.DoesNotExist):
            ReviewNoteSelector.get_by_id(str(note.id))


@pytest.mark.django_db
class TestDecisionOverrideOptimisticLocking:
    """Tests for optimistic locking in DecisionOverride."""

    def test_update_decision_override_version_conflict_raises_error(
        self,
        decision_override_service,
        paid_case,
        eligibility_result,
    ):
        """Updating with wrong version should raise ValidationError."""
        case, _payment = paid_case
        override = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="initial override",
        )
        assert override is not None
        initial_version = override.version
        
        DecisionOverrideRepository.update_decision_override(
            override,
            version=initial_version,
            reason="updated reason",
        )
        
        with pytest.raises(ValidationError) as exc_info:
            DecisionOverrideRepository.update_decision_override(
                override,
                version=initial_version,  # Stale version
                reason="stale update",
            )
        
        assert "modified by another user" in str(exc_info.value).lower()
