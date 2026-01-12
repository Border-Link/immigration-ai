"""
Admin API Views for Payment Analytics and Statistics

Admin-only endpoints for payment analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from payments.services.payment_service import PaymentService


class PaymentStatisticsAPI(AuthAPI):
    """
    Admin: Get payment statistics and analytics.
    
    Endpoint: GET /api/v1/payments/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        statistics = PaymentService.get_statistics()
        
        return self.api_response(
            message="Payment statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )
