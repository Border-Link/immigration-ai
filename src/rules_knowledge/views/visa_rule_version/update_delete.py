from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_permission import RulePermission
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer
from rules_knowledge.serializers.visa_rule_version.update_delete import VisaRuleVersionUpdateSerializer


class VisaRuleVersionUpdateAPI(AuthAPI):
    """Update a visa rule version. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def patch(self, request, id):
        serializer = VisaRuleVersionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract version for optimistic locking if provided
        expected_version = serializer.validated_data.pop('version', None)
        updated_by = request.user if request.user.is_authenticated else None
        
        rule_version = VisaRuleVersionService.update_rule_version(
            id, updated_by=updated_by, expected_version=expected_version, **serializer.validated_data
        )
        
        if not rule_version:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa rule version updated successfully.",
            data=VisaRuleVersionSerializer(rule_version).data,
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionDeleteAPI(AuthAPI):
    """Delete a visa rule version. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def delete(self, request, id):
        success = VisaRuleVersionService.delete_visa_rule_version(id)
        if not success:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa rule version deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

