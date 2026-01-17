from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from main_system.repositories.base import BaseRepositoryMixin
from human_reviews.models.review_note import ReviewNote
from human_reviews.models.review import Review


class ReviewNoteRepository:
    """Repository for ReviewNote write operations."""

    @staticmethod
    def create_review_note(review: Review, note: str, is_internal: bool = False):
        """Create a new review note."""
        with transaction.atomic():
            review_note = ReviewNote.objects.create(
                review=review,
                note=note,
                is_internal=is_internal
            )
            review_note.full_clean()
            review_note.save()
            return review_note

    @staticmethod
    def update_review_note(review_note, version: int = None, **fields):
        """
        Update review note fields with optimistic locking.
        
        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(review_note, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in ReviewNote._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            updated_count = ReviewNote.objects.filter(
                id=review_note.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ReviewNote.objects.filter(id=review_note.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Review note not found.")
                raise ValidationError(
                    f"Review note was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ReviewNote.objects.get(id=review_note.id)

    @staticmethod
    def soft_delete_review_note(review_note, version: int = None, deleted_by=None) -> ReviewNote:
        """
        Soft delete a review note with optimistic locking.
        
        Args:
            review_note: ReviewNote instance to soft delete
            version: Expected version number for optimistic locking
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted ReviewNote instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(review_note, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ReviewNote.objects.filter(
                id=review_note.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ReviewNote.objects.filter(id=review_note.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Review note not found.")
                raise ValidationError(
                    f"Review note was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ReviewNote.objects.get(id=review_note.id)
    
    @staticmethod
    def delete_review_note(review_note, version: int = None, deleted_by=None):
        """
        Delete a review note (soft delete).
        
        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        ReviewNoteRepository.soft_delete_review_note(review_note, version=version, deleted_by=deleted_by)
        return True
    
    @staticmethod
    def restore_review_note(review_note, version: int = None, restored_by=None) -> ReviewNote:
        """
        Restore a soft-deleted review note with optimistic locking.
        
        Args:
            review_note: ReviewNote instance to restore
            version: Expected version number for optimistic locking
            restored_by: User performing the restoration
            
        Returns:
            Restored ReviewNote instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(review_note, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ReviewNote.objects.filter(
                id=review_note.id,
                version=expected_version,
                is_deleted=True,
            ).update(
                is_deleted=False,
                deleted_at=None,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ReviewNote.objects.filter(id=review_note.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Review note not found.")
                raise ValidationError(
                        f"Review note was modified by another user. Expected version {expected_version}, got {current_version}."
                    )

            return ReviewNote.objects.get(id=review_note.id)

