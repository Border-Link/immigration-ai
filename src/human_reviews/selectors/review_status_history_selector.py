"""
Selector for ReviewStatusHistory read operations.
"""
from human_reviews.models.review_status_history import ReviewStatusHistory
from human_reviews.models.review import Review


class ReviewStatusHistorySelector:
    """Selector for ReviewStatusHistory read operations."""

    @staticmethod
    def get_all():
        """Get all status history entries."""
        return ReviewStatusHistory.objects.select_related(
            'review',
            'review__case',
            'changed_by'
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_review(review: Review):
        """Get status history by review."""
        return ReviewStatusHistory.objects.select_related(
            'review',
            'review__case',
            'changed_by'
        ).filter(review=review, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(history_id):
        """Get status history by ID."""
        return ReviewStatusHistory.objects.select_related(
            'review',
            'review__case',
            'changed_by'
        ).filter(is_deleted=False).get(id=history_id)

    @staticmethod
    def get_by_review_id(review_id: str):
        """Get status history by review ID."""
        return ReviewStatusHistory.objects.select_related(
            'review',
            'review__case',
            'changed_by'
        ).filter(review_id=review_id, is_deleted=False).order_by('-created_at')
