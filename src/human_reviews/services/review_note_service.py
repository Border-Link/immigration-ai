import logging
from typing import Optional
from helpers.cache_utils import cache_result
from human_reviews.models.review_note import ReviewNote
from human_reviews.repositories.review_note_repository import ReviewNoteRepository
from human_reviews.selectors.review_note_selector import ReviewNoteSelector
from human_reviews.selectors.review_selector import ReviewSelector

logger = logging.getLogger('django')


class ReviewNoteService:
    """Service for ReviewNote business logic."""

    @staticmethod
    def create_review_note(review_id: str, note: str, is_internal: bool = False) -> Optional[ReviewNote]:
        """Create a new review note."""
        try:
            review = ReviewSelector.get_by_id(review_id)
            return ReviewNoteRepository.create_review_note(review, note, is_internal)
        except Exception as e:
            logger.error(f"Error creating review note: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - notes change when reviewers add notes
    def get_all():
        """Get all review notes."""
        try:
            return ReviewNoteSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all review notes: {e}")
            return ReviewNote.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['review_id'])  # 5 minutes - cache notes by review
    def get_by_review(review_id: str):
        """Get notes by review."""
        try:
            review = ReviewSelector.get_by_id(review_id)
            return ReviewNoteSelector.get_by_review(review)
        except Exception as e:
            logger.error(f"Error fetching notes for review {review_id}: {e}")
            return ReviewNote.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['review_id'])  # 5 minutes - cache public notes by review
    def get_public_by_review(review_id: str):
        """Get public notes (not internal) by review."""
        try:
            review = ReviewSelector.get_by_id(review_id)
            return ReviewNoteSelector.get_public_by_review(review)
        except Exception as e:
            logger.error(f"Error fetching public notes for review {review_id}: {e}")
            return ReviewNote.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['note_id'])  # 10 minutes - cache note by ID
    def get_by_id(note_id: str) -> Optional[ReviewNote]:
        """Get review note by ID."""
        try:
            return ReviewNoteSelector.get_by_id(note_id)
        except ReviewNote.DoesNotExist:
            logger.error(f"Review note {note_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching review note {note_id}: {e}")
            return None

    @staticmethod
    def update_review_note(note_id: str, **fields) -> Optional[ReviewNote]:
        """Update review note fields."""
        try:
            review_note = ReviewNoteSelector.get_by_id(note_id)
            return ReviewNoteRepository.update_review_note(review_note, **fields)
        except ReviewNote.DoesNotExist:
            logger.error(f"Review note {note_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating review note {note_id}: {e}")
            return None

    @staticmethod
    def delete_review_note(note_id: str) -> bool:
        """Delete a review note."""
        try:
            review_note = ReviewNoteSelector.get_by_id(note_id)
            ReviewNoteRepository.delete_review_note(review_note)
            return True
        except ReviewNote.DoesNotExist:
            logger.error(f"Review note {note_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting review note {note_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(review_id=None, is_internal=None, date_from=None, date_to=None):
        """Get review notes with advanced filtering for admin."""
        try:
            return ReviewNoteSelector.get_by_filters(
                review_id=review_id,
                is_internal=is_internal,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering review notes: {e}")
            return ReviewNote.objects.none()
