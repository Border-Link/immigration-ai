"""
Admin API Views for Compliance Analytics and Statistics

Admin-only endpoints for compliance analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')


class ComplianceStatisticsAPI(AuthAPI):
    """
    Admin: Get compliance statistics and analytics.
    
    Endpoint: GET /api/v1/compliance/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        try:
            audit_log_stats = AuditLogService.get_statistics()
            
            statistics = {
                'audit_logs': audit_log_stats,
            }
            
            return self.api_response(
                message="Compliance statistics retrieved successfully.",
                data=statistics,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving compliance statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving compliance statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
