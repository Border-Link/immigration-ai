from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from payments.services.payment_service import PaymentService
from payments.serializers.payment.read import PaymentSerializer, PaymentListSerializer


class PaymentListAPI(AuthAPI):
    """Get list of payments. Supports filtering by case_id, status."""
    permission_classes = [PaymentPermission]

    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        status_filter = request.query_params.get('status', None)

        # Security: regular users only see their own payments; staff can see all.
        if case_id:
            payments = PaymentService.get_by_case(str(case_id))
        elif status_filter:
            payments = PaymentService.get_by_status(status_filter)
        else:
            payments = PaymentService.get_all() if request.user.is_staff else PaymentService.get_by_user(request.user)

        return self.api_response(
            message="Payments retrieved successfully.",
            data=PaymentListSerializer(payments, many=True).data,
            status_code=status.HTTP_200_OK
        )


class PaymentDetailAPI(AuthAPI):
    """Get payment by ID."""
    permission_classes = [PaymentPermission]

    def get(self, request, id):
        payment = PaymentService.get_by_id(str(id))
        if not payment:
            return self.api_response(
                message=f"Payment with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Enforce object-level access control (PaymentPermission.has_object_permission)
        self.check_object_permissions(request, payment)

        return self.api_response(
            message="Payment retrieved successfully.",
            data=PaymentSerializer(payment).data,
            status_code=status.HTTP_200_OK
        )

