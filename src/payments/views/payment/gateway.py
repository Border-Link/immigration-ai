"""
Payment Gateway Views

Views for initiating payments, verifying payment status, and processing refunds.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from payments.services.payment_service import PaymentService
from payments.serializers.payment.read import PaymentSerializer
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError

logger = logging.getLogger('django')


class PaymentInitiateAPI(AuthAPI):
    """
    Initiate payment with payment gateway.
    
    Endpoint: POST /api/v1/payments/<id>/initiate/
    """
    permission_classes = [PaymentPermission]
    
    def post(self, request, id):
        existing = PaymentService.get_by_id(str(id))
        if not existing:
            return self.api_response(
                message="Failed to initiate payment.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, existing)

        return_url = request.data.get('return_url')
        callback_url = request.data.get('callback_url')
        
        result = PaymentService.initiate_payment(
            payment_id=str(id),
            return_url=return_url,
            callback_url=callback_url
        )
        
        if not result:
            return self.api_response(
                message="Failed to initiate payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return self.api_response(
            message="Payment initiated successfully.",
            data=result,
            status_code=status.HTTP_200_OK
        )


class PaymentVerifyAPI(AuthAPI):
    """
    Verify payment status with payment gateway.
    
    Endpoint: POST /api/v1/payments/<id>/verify/
    """
    permission_classes = [PaymentPermission]
    
    def post(self, request, id):
        existing = PaymentService.get_by_id(str(id))
        if not existing:
            return self.api_response(
                message="Failed to verify payment.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, existing)

        result = PaymentService.verify_payment_status(payment_id=str(id))
        
        if not result:
            return self.api_response(
                message="Failed to verify payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get updated payment
        payment = PaymentService.get_by_id(str(id))
        
        return self.api_response(
            message="Payment verified successfully.",
            data={
                'payment': PaymentSerializer(payment).data if payment else None,
                'verification': result,
            },
            status_code=status.HTTP_200_OK
        )


class PaymentRefundAPI(AuthAPI):
    """
    Process a refund for a payment.
    
    Endpoint: POST /api/v1/payments/<id>/refund/
    """
    permission_classes = [PaymentPermission]
    
    def post(self, request, id):
        from decimal import Decimal
        from payments.serializers.payment.refund import PaymentRefundSerializer

        existing = PaymentService.get_by_id(str(id))
        if not existing:
            return self.api_response(
                message="Failed to process refund.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, existing)
        
        serializer = PaymentRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data.get('amount')
        reason = serializer.validated_data.get('reason')
        
        result = PaymentService.process_refund(
            payment_id=str(id),
            amount=Decimal(str(amount)) if amount else None,
            reason=reason
        )
        
        if not result:
            return self.api_response(
                message="Failed to process refund.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get updated payment
        payment = PaymentService.get_by_id(str(id))
        
        return self.api_response(
            message="Refund processed successfully.",
            data={
                'payment': PaymentSerializer(payment).data if payment else None,
                'refund': result,
            },
            status_code=status.HTTP_200_OK
        )
