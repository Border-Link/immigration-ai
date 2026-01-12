"""
Admin API Views for Human Reviews Analytics and Statistics

Admin-only endpoints for human reviews analytics, statistics, and reporting.
Access restricted to staff/superusers using AdminPermission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from human_reviews.services.review_service import ReviewService


class HumanReviewsStatisticsAPI(AuthAPI):
    """
    Admin: Get human reviews statistics and analytics.
    
    Endpoint: GET /api/v1/human-reviews/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        statistics = ReviewService.get_statistics()
        
        return self.api_response(
            message="Human reviews statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )
