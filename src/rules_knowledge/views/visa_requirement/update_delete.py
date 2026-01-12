from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_permission import RulePermission
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.serializers.visa_requirement.read import VisaRequirementSerializer
from rules_knowledge.serializers.visa_requirement.update_delete import VisaRequirementUpdateSerializer


class VisaRequirementUpdateAPI(AuthAPI):
    """Update a visa requirement. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def patch(self, request, id):
        serializer = VisaRequirementUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requirement = VisaRequirementService.update_visa_requirement(id, **serializer.validated_data)
        if not requirement:
            return self.api_response(
                message=f"Visa requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa requirement updated successfully.",
            data=VisaRequirementSerializer(requirement).data,
            status_code=status.HTTP_200_OK
        )


class VisaRequirementDeleteAPI(AuthAPI):
    """Delete a visa requirement. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def delete(self, request, id):
        success = VisaRequirementService.delete_visa_requirement(id)
        if not success:
            return self.api_response(
                message=f"Visa requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa requirement deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

