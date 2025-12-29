from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.serializers.visa_requirement.create import VisaRequirementCreateSerializer
from rules_knowledge.serializers.visa_requirement.read import VisaRequirementSerializer


class VisaRequirementCreateAPI(AuthAPI):
    """Create a new visa requirement. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = VisaRequirementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requirement = VisaRequirementService.create_visa_requirement(
            rule_version_id=serializer.validated_data.get('rule_version_id'),
            requirement_code=serializer.validated_data.get('requirement_code'),
            description=serializer.validated_data.get('description'),
            condition_expression=serializer.validated_data.get('condition_expression'),
            is_active=serializer.validated_data.get('is_active', True)
        )

        if not requirement:
            return self.api_response(
                message="Visa requirement already exists or error creating requirement.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Visa requirement created successfully.",
            data=VisaRequirementSerializer(requirement).data,
            status_code=status.HTTP_201_CREATED
        )

