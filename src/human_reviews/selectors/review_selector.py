from human_reviews.models.review import Review
from immigration_cases.models.case import Case
from django.conf import settings


class ReviewSelector:
    """Selector for Review read operations."""

    @staticmethod
    def get_all():
        """Get all reviews."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get reviews by case."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str):
        """Get reviews by status."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).filter(status=status).order_by('-created_at')

    @staticmethod
    def get_by_reviewer(reviewer):
        """Get reviews by reviewer."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).filter(reviewer=reviewer).order_by('-created_at')

    @staticmethod
    def get_pending_by_reviewer(reviewer):
        """Get pending/in_progress reviews by reviewer."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).filter(
            reviewer=reviewer,
            status__in=['pending', 'in_progress']
        ).order_by('-created_at')

    @staticmethod
    def get_by_id(review_id):
        """Get review by ID."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).get(id=review_id)

    @staticmethod
    def get_pending():
        """Get all pending reviews (not assigned)."""
        return Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).filter(status='pending', reviewer__isnull=True).order_by('-created_at')

