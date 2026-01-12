from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_permission import RulePermission
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.create import VisaRuleVersionCreateSerializer
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer


class VisaRuleVersionCreateAPI(AuthAPI):
    """Create a new visa rule version. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def post(self, request):
        serializer = VisaRuleVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_by = request.user if request.user.is_authenticated else None
        rule_version = VisaRuleVersionService.create_rule_version(
            visa_type_id=serializer.validated_data.get('visa_type_id'),
            effective_from=serializer.validated_data.get('effective_from'),
            effective_to=serializer.validated_data.get('effective_to'),
            source_document_version_id=serializer.validated_data.get('source_document_version_id'),
            created_by=created_by
        )

        if not rule_version:
            return self.api_response(
                message="Error creating visa rule version.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Visa rule version created successfully.",
            data=VisaRuleVersionSerializer(rule_version).data,
            status_code=status.HTTP_201_CREATED
        )

