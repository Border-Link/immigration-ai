from rest_framework import status
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer
from immigration_cases.serializers.case.update_delete import CaseUpdateSerializer


class CaseUpdateAPI(AuthAPI):
    """Update a case."""

    def patch(self, request, id):
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

    def delete(self, request, id):
        success = CaseService.delete_case(id)
        if not success:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

