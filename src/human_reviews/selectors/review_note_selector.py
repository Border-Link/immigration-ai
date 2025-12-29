from human_reviews.models.review_note import ReviewNote
from human_reviews.models.review import Review


class ReviewNoteSelector:
    """Selector for ReviewNote read operations."""

    @staticmethod
    def get_all():
        """Get all review notes."""
        return ReviewNote.objects.select_related(
            'review',
            'review__case',
            'review__case__user',
            'review__reviewer'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_review(review: Review):
        """Get notes by review."""
        return ReviewNote.objects.select_related(
            'review',
            'review__case',
            'review__case__user',
            'review__reviewer'
        ).filter(review=review).order_by('-created_at')

    @staticmethod
    def get_public_by_review(review: Review):
        """Get public notes (not internal) by review."""
        return ReviewNote.objects.select_related(
            'review',
            'review__case',
            'review__case__user',
            'review__reviewer'
        ).filter(review=review, is_internal=False).order_by('-created_at')

    @staticmethod
    def get_by_id(note_id):
        """Get review note by ID."""
        return ReviewNote.objects.select_related(
            'review',
            'review__case',
            'review__case__user',
            'review__reviewer'
        ).get(id=note_id)

