"""
Admin API Views for Human Reviews Analytics and Statistics

Admin-only endpoints for human reviews analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from human_reviews.services.review_service import ReviewService
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.services.decision_override_service import DecisionOverrideService
from human_reviews.models.review import Review
from human_reviews.models.review_note import ReviewNote
from human_reviews.models.decision_override import DecisionOverride
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta


class HumanReviewsStatisticsAPI(AuthAPI):
    """
    Admin: Get human reviews statistics and analytics.
    
    Endpoint: GET /api/v1/human-reviews/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
            # Review statistics
            total_reviews = Review.objects.count()
            reviews_by_status = Review.objects.values('status').annotate(count=Count('id'))
            pending_reviews = Review.objects.filter(status='pending').count()
            in_progress_reviews = Review.objects.filter(status='in_progress').count()
            completed_reviews = Review.objects.filter(status='completed').count()
            cancelled_reviews = Review.objects.filter(status='cancelled').count()
            
            # Reviews with assigned reviewers
            assigned_reviews = Review.objects.filter(reviewer__isnull=False).count()
            unassigned_reviews = Review.objects.filter(reviewer__isnull=True).count()
            
            # Average time to completion
            completed_reviews_with_times = Review.objects.filter(
                status='completed',
                completed_at__isnull=False,
                assigned_at__isnull=False
            )
            avg_completion_time = None
            if completed_reviews_with_times.exists():
                time_diffs = []
                for review in completed_reviews_with_times:
                    if review.assigned_at and review.completed_at:
                        diff = review.completed_at - review.assigned_at
                        time_diffs.append(diff.total_seconds() / 3600)  # Convert to hours
                if time_diffs:
                    avg_completion_time = sum(time_diffs) / len(time_diffs)
            
            # Review note statistics
            total_notes = ReviewNote.objects.count()
            internal_notes = ReviewNote.objects.filter(is_internal=True).count()
            public_notes = ReviewNote.objects.filter(is_internal=False).count()
            notes_per_review = ReviewNote.objects.values('review').annotate(count=Count('id'))
            avg_notes_per_review = notes_per_review.aggregate(avg=Avg('count'))['avg'] or 0.0
            
            # Decision override statistics
            total_overrides = DecisionOverride.objects.count()
            overrides_by_outcome = DecisionOverride.objects.values('overridden_outcome').annotate(count=Count('id'))
            overrides_with_reviewer = DecisionOverride.objects.filter(reviewer__isnull=False).count()
            
            # Recent activity (last 7 days)
            seven_days_ago = timezone.now() - timedelta(days=7)
            recent_reviews = Review.objects.filter(created_at__gte=seven_days_ago).count()
            recent_completions = Review.objects.filter(
                status='completed',
                completed_at__gte=seven_days_ago
            ).count()
            recent_overrides = DecisionOverride.objects.filter(created_at__gte=seven_days_ago).count()
            
            # Reviewer workload
            reviewer_workload = Review.objects.filter(
                reviewer__isnull=False,
                status__in=['pending', 'in_progress']
            ).values('reviewer__email').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            statistics = {
                'reviews': {
                    'total': total_reviews,
                    'by_status': {item['status']: item['count'] for item in reviews_by_status},
                    'pending': pending_reviews,
                    'in_progress': in_progress_reviews,
                    'completed': completed_reviews,
                    'cancelled': cancelled_reviews,
                    'assigned': assigned_reviews,
                    'unassigned': unassigned_reviews,
                    'average_completion_time_hours': round(avg_completion_time, 2) if avg_completion_time else None,
                },
                'review_notes': {
                    'total': total_notes,
                    'internal': internal_notes,
                    'public': public_notes,
                    'average_per_review': round(avg_notes_per_review, 2),
                },
                'decision_overrides': {
                    'total': total_overrides,
                    'by_outcome': {item['overridden_outcome']: item['count'] for item in overrides_by_outcome},
                    'with_reviewer': overrides_with_reviewer,
                },
                'recent_activity': {
                    'last_7_days': {
                        'reviews_created': recent_reviews,
                        'reviews_completed': recent_completions,
                        'overrides_created': recent_overrides,
                    }
                },
                'reviewer_workload': [
                    {
                        'reviewer_email': item['reviewer__email'],
                        'active_reviews': item['count']
                    }
                    for item in reviewer_workload
                ],
            }
            
        return self.api_response(
            message="Human reviews statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )
