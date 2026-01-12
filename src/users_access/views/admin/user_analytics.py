"""
Admin API Views for User Analytics and Statistics

Admin-only endpoints for user analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.user_service import UserService


class UserStatisticsAPI(AuthAPI):
    """
    Admin: Get user statistics and analytics.
    
    Endpoint: GET /api/v1/auth/admin/users/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        statistics = UserService.get_statistics()
        
        return self.api_response(
            message="User statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )


class UserActivityAPI(AuthAPI):
    """
    Admin: Get user activity information.
    
    Endpoint: GET /api/v1/auth/admin/users/<id>/activity/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request, id):
        activity = UserService.get_user_activity(id)
        
        if not activity:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="User activity retrieved successfully.",
            data=activity,
            status_code=status.HTTP_200_OK
        )
