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

    @staticmethod
    def get_by_filters(case_id=None, reviewer_id=None, status=None, date_from=None, date_to=None, assigned_date_from=None, assigned_date_to=None, completed_date_from=None, completed_date_to=None):
        """Get reviews with advanced filtering for admin."""
        queryset = Review.objects.select_related(
            'case',
            'case__user',
            'reviewer',
            'reviewer__profile'
        ).all()
        
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if assigned_date_from:
            queryset = queryset.filter(assigned_at__gte=assigned_date_from)
        
        if assigned_date_to:
            queryset = queryset.filter(assigned_at__lte=assigned_date_to)
        
        if completed_date_from:
            queryset = queryset.filter(completed_at__gte=completed_date_from)
        
        if completed_date_to:
            queryset = queryset.filter(completed_at__lte=completed_date_to)
        
        return queryset.order_by('-created_at')
