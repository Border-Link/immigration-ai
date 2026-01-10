"""
Admin API Views for User Analytics and Statistics

Admin-only endpoints for user analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from users_access.services.user_service import UserService
from users_access.models.user import User

logger = logging.getLogger('django')


class UserStatisticsAPI(AuthAPI):
    """
    Admin: Get user statistics and analytics.
    
    Endpoint: GET /api/v1/auth/admin/users/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        try:
            statistics = UserService.get_statistics()
            
            return self.api_response(
                message="User statistics retrieved successfully.",
                data=statistics,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving user statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving user statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserActivityAPI(AuthAPI):
    """
    Admin: Get user activity information.
    
    Endpoint: GET /api/v1/auth/admin/users/<id>/activity/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving user activity {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving user activity.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
