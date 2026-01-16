from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from payments.services.payment_service import PaymentService
from payments.serializers.payment.read import PaymentSerializer
from payments.serializers.payment.update_delete import PaymentUpdateSerializer


class PaymentUpdateAPI(AuthAPI):
    """Update a payment."""
    permission_classes = [PaymentPermission]

    def patch(self, request, id):
        serializer = PaymentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version = serializer.validated_data.pop('version', None)

        # Enforce object-level access control
        existing = PaymentService.get_by_id(str(id))
        if not existing:
            return self.api_response(
                message=f"Payment with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, existing)

        payment = PaymentService.update_payment(
            payment_id=str(id),
            version=version,
            changed_by=request.user,
            **serializer.validated_data
        )
        
        if not payment:
            return self.api_response(
                message=f"Payment with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Payment updated successfully.",
            data=PaymentSerializer(payment).data,
            status_code=status.HTTP_200_OK
        )


class PaymentDeleteAPI(AuthAPI):
    """Delete a payment."""
    permission_classes = [PaymentPermission]

    def delete(self, request, id):
        # Enforce object-level access control
        existing = PaymentService.get_by_id(str(id))
        if not existing:
            return self.api_response(
                message=f"Payment with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, existing)

        success = PaymentService.delete_payment(
            payment_id=str(id),
            changed_by=request.user,
            reason="Deleted by user"
        )
        
        if not success:
            return self.api_response(
                message=f"Payment with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Payment deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

