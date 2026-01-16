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

    @staticmethod
    def get_by_filters(review_id=None, is_internal=None, date_from=None, date_to=None):
        """Get review notes with advanced filtering for admin."""
        queryset = ReviewNote.objects.select_related(
            'review',
            'review__case',
            'review__case__user',
            'review__reviewer'
        ).all()
        
        if review_id:
            queryset = queryset.filter(review_id=review_id)
        
        if is_internal is not None:
            queryset = queryset.filter(is_internal=is_internal)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_none():
        """Return an empty queryset."""
        return ReviewNote.objects.none()
