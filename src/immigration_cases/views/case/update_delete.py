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

        case = CaseService.update_case(id, **serializer.validated_data)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case updated successfully.",
            data=CaseSerializer(case).data,
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

