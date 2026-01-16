"""
Payment History Views

Views for accessing payment history.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from payments.services.payment_service import PaymentService
from payments.services.payment_history_service import PaymentHistoryService
from payments.serializers.payment.history import PaymentHistorySerializer
from payments.serializers.payment.read import PaymentSerializer


class PaymentHistoryAPI(AuthAPI):
    """
    Get payment history for a payment.
    
    Endpoint: GET /api/v1/payments/<id>/history/
    """
    permission_classes = [PaymentPermission]
    
    def get(self, request, id):
        # Verify payment exists and user has access
        payment = PaymentService.get_by_id(str(id))
        if not payment:
            return self.api_response(
                message="Payment not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Enforce object-level access control
        self.check_object_permissions(request, payment)
        
        history = PaymentHistoryService.get_by_payment(str(id))
        
        return self.api_response(
            message="Payment history retrieved successfully.",
            data=PaymentHistorySerializer(history, many=True).data,
            status_code=status.HTTP_200_OK
        )


class PaymentRetryAPI(AuthAPI):
    """
    Retry a failed payment.
    
    Endpoint: POST /api/v1/payments/<id>/retry/
    """
    permission_classes = [PaymentPermission]
    
    def post(self, request, id):
        from payments.services.payment_retry_service import PaymentRetryService
        
        # Verify payment exists and user has access
        payment = PaymentService.get_by_id(str(id))
        if not payment:
            return self.api_response(
                message="Payment not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Enforce object-level access control
        self.check_object_permissions(request, payment)
        
        result = PaymentRetryService.retry_payment(str(id))
        
        if not result:
            return self.api_response(
                message="Failed to retry payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if not result.get('success'):
            return self.api_response(
                message=result.get('error', 'Failed to retry payment.'),
                data=result,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get updated payment
        updated_payment = PaymentService.get_by_id(str(id))
        
        return self.api_response(
            message="Payment retry initiated successfully.",
            data={
                'payment': PaymentSerializer(updated_payment).data if updated_payment else None,
                'retry_result': result,
            },
            status_code=status.HTTP_200_OK
        )
