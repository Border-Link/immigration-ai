from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.case_permission import CasePermission
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer
from immigration_cases.serializers.case.update_delete import CaseUpdateSerializer


class CaseUpdateAPI(AuthAPI):
    """Update a case."""
    permission_classes = [CasePermission]

    def patch(self, request, id):
        # Fetch entity first to enforce object-level permissions
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, case)

        serializer = CaseUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract version and reason for optimistic locking and history tracking
        version = serializer.validated_data.pop('version', None)
        reason = serializer.validated_data.pop('reason', None)
        
        updated_case, error_message, http_status = CaseService.update_case(
            id,
            updated_by_id=str(request.user.id) if request.user else None,
            reason=reason,
            version=version,
            **serializer.validated_data
        )
        
        if not updated_case:
            status_code = status.HTTP_404_NOT_FOUND if http_status == 404 else (
                status.HTTP_409_CONFLICT if http_status == 409 else (
                    status.HTTP_400_BAD_REQUEST if http_status == 400 else status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            )
            return self.api_response(
                message=error_message or f"Case with ID '{id}' not found.",
                data=None,
                status_code=status_code
            )

        return self.api_response(
            message="Case updated successfully.",
            data=CaseSerializer(updated_case).data,
            status_code=status.HTTP_200_OK
        )


class CaseDeleteAPI(AuthAPI):
    """Delete a case."""
    permission_classes = [CasePermission]

    def delete(self, request, id):
        # Fetch entity first to enforce object-level permissions
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, case)

        # Return correct error semantics for payment-gated operations
        from payments.helpers.payment_validator import PaymentValidator
        is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="case deletion")
        if not is_valid:
            return self.api_response(
                message=error,
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        success = CaseService.delete_case(id, deleted_by_id=str(request.user.id) if request.user else None)
        if not success:
            return self.api_response(
                message="Failed to delete case.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return self.api_response(
            message="Case deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

