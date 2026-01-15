from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.case_fact_permission import CaseFactPermission
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.serializers.case_fact.read import CaseFactSerializer
from immigration_cases.serializers.case_fact.update_delete import CaseFactUpdateSerializer


class CaseFactUpdateAPI(AuthAPI):
    """Update a case fact."""
    permission_classes = [CaseFactPermission]

    def patch(self, request, id):
        # Fetch entity first to enforce object-level permissions
        fact = CaseFactService.get_by_id(id)
        if not fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, fact)

        serializer = CaseFactUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fact = CaseFactService.update_case_fact(id, **serializer.validated_data)
        if not fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case fact updated successfully.",
            data=CaseFactSerializer(fact).data,
            status_code=status.HTTP_200_OK
        )


class CaseFactDeleteAPI(AuthAPI):
    """Delete a case fact."""
    permission_classes = [CaseFactPermission]

    def delete(self, request, id):
        # Fetch entity first to enforce object-level permissions
        fact = CaseFactService.get_by_id(id)
        if not fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, fact)

        success = CaseFactService.delete_case_fact(id)
        if not success:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case fact deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

