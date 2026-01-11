"""
Repository for ReviewStatusHistory write operations.
"""
from django.db import transaction
from human_reviews.models.review_status_history import ReviewStatusHistory
from human_reviews.models.review import Review
from django.conf import settings


class ReviewStatusHistoryRepository:
    """Repository for ReviewStatusHistory write operations."""

    @staticmethod
    def create_status_history(review: Review, previous_status: str, new_status: str,
                              changed_by=None, reason: str = None, metadata: dict = None):
        """Create a new status history entry."""
        with transaction.atomic():
            history = ReviewStatusHistory.objects.create(
                review=review,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
                reason=reason,
                metadata=metadata or {}
            )
            history.full_clean()
            history.save()
            return history
