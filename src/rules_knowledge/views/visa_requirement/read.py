from rest_framework import status
from main_system.base.auth_api import AuthAPI
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.serializers.visa_requirement.read import VisaRequirementSerializer, VisaRequirementListSerializer


class VisaRequirementListAPI(AuthAPI):
    """Get list of visa requirements. Supports filtering by rule_version_id."""

    def get(self, request):
        rule_version_id = request.query_params.get('rule_version_id', None)

        if rule_version_id:
            requirements = VisaRequirementService.get_by_rule_version(rule_version_id)
        else:
            requirements = VisaRequirementService.get_all()

        return self.api_response(
            message="Visa requirements retrieved successfully.",
            data=VisaRequirementListSerializer(requirements, many=True).data,
            status_code=status.HTTP_200_OK
        )


class VisaRequirementDetailAPI(AuthAPI):
    """Get visa requirement by ID."""

    def get(self, request, id):
        requirement = VisaRequirementService.get_by_id(id)
        if not requirement:
            return self.api_response(
                message=f"Visa requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa requirement retrieved successfully.",
            data=VisaRequirementSerializer(requirement).data,
            status_code=status.HTTP_200_OK
        )

