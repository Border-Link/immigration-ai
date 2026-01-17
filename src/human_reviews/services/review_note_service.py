from __future__ import annotations

import logging
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from main_system.utils.cache_utils import cache_result, invalidate_cache
from human_reviews.repositories.review_note_repository import ReviewNoteRepository
from human_reviews.selectors.review_note_selector import ReviewNoteSelector
from human_reviews.selectors.review_selector import ReviewSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "review_notes"


class ReviewNoteService:
    """Service for ReviewNote business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda n: n is not None)
    def create_review_note(review_id: str, note: str, is_internal: bool = False) -> Optional[ReviewNote]:
        """
        Create a new review note.
        
        Requires: Case must have a completed payment before review notes can be created.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate reviewer add-on payment requirement (human reviews are an add-on)
            is_valid, error = PaymentValidator.validate_case_has_reviewer_addon(
                review.case,
                operation_name="review note creation",
            )
            if not is_valid:
                logger.warning(f"Review note creation blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            return ReviewNoteRepository.create_review_note(review, note, is_internal)
        except Exception as e:
            logger.error(f"Error creating review note: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")  # 5 minutes - notes change when reviewers add notes
    def get_all():
        """Get all review notes."""
        try:
            return ReviewNoteSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all review notes: {e}")
            return ReviewNoteSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['review_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache notes by review
    def get_by_review(review_id: str):
        """Get notes by review."""
        try:
            review = ReviewSelector.get_by_id(review_id)
            return ReviewNoteSelector.get_by_review(review)
        except Exception as e:
            logger.error(f"Error fetching notes for review {review_id}: {e}")
            return ReviewNoteSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['review_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache public notes by review
    def get_public_by_review(review_id: str):
        """Get public notes (not internal) by review."""
        try:
            review = ReviewSelector.get_by_id(review_id)
            return ReviewNoteSelector.get_public_by_review(review)
        except Exception as e:
            logger.error(f"Error fetching public notes for review {review_id}: {e}")
            return ReviewNoteSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['note_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache note by ID
    def get_by_id(note_id: str) -> Optional[ReviewNote]:
        """Get review note by ID."""
        try:
            return ReviewNoteSelector.get_by_id(note_id)
        except ObjectDoesNotExist:
            logger.error(f"Review note {note_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching review note {note_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda n: n is not None)
    def update_review_note(note_id: str, version: int = None, **fields) -> Optional[ReviewNote]:
        """
        Update review note fields with optimistic locking.
        
        Requires: Case must have a completed payment before review notes can be updated.
        
        Args:
            note_id: ID of the note to update
            version: Expected version number for optimistic locking (required)
            **fields: Fields to update
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review_note = ReviewNoteSelector.get_by_id(note_id)
            if not review_note:
                logger.error(f"Review note {note_id} not found")
                return None
            
            # Validate reviewer add-on payment requirement (human reviews are an add-on)
            is_valid, error = PaymentValidator.validate_case_has_reviewer_addon(
                review_note.review.case, 
                operation_name="review note update"
            )
            if not is_valid:
                logger.warning(f"Review note update blocked for case {review_note.review.case.id}: {error}")
                raise ValidationError(error)
            
            # Use version from parameter or from the note
            update_version = version if version is not None else review_note.version
            
            return ReviewNoteRepository.update_review_note(review_note, version=update_version, **fields)
        except ValidationError as e:
            logger.warning(f"Version conflict or validation error updating review note {note_id}: {e}")
            raise
        except ObjectDoesNotExist:
            logger.error(f"Review note {note_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating review note {note_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_review_note(note_id: str, version: int = None, deleted_by=None) -> bool:
        """
        Soft delete a review note.
        
        Requires: Case must have a completed payment before review notes can be deleted.
        This prevents abuse and ensures only paid cases can manage their review notes.
        
        Args:
            note_id: ID of the note to delete
            version: Expected version number for optimistic locking (required)
            deleted_by: User performing the deletion
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review_note = ReviewNoteSelector.get_by_id(note_id)
            if not review_note:
                logger.error(f"Review note {note_id} not found")
                return False
            
            # Validate reviewer add-on payment requirement (human reviews are an add-on)
            is_valid, error = PaymentValidator.validate_case_has_reviewer_addon(
                review_note.review.case, 
                operation_name="review note deletion"
            )
            if not is_valid:
                logger.warning(f"Review note deletion blocked for case {review_note.review.case.id}: {error}")
                raise ValidationError(error)
            
            # Use version from parameter or from the note
            delete_version = version if version is not None else review_note.version
            
            ReviewNoteRepository.delete_review_note(review_note, version=delete_version, deleted_by=deleted_by)
            return True
        except ValidationError as e:
            logger.warning(f"Version conflict or validation error deleting review note {note_id}: {e}")
            raise
        except ObjectDoesNotExist:
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
            return ReviewNoteSelector.get_none()
