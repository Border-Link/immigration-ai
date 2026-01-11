from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.serializers.visa_document_requirement.create import VisaDocumentRequirementCreateSerializer
from rules_knowledge.serializers.visa_document_requirement.read import VisaDocumentRequirementSerializer


class VisaDocumentRequirementCreateAPI(AuthAPI):
    """Create a new visa document requirement. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = VisaDocumentRequirementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_requirement = VisaDocumentRequirementService.create_visa_document_requirement(
            rule_version_id=serializer.validated_data.get('rule_version_id'),
            document_type_id=serializer.validated_data.get('document_type_id'),
            mandatory=serializer.validated_data.get('mandatory', True),
            description=serializer.validated_data.get('description')
        )

        if not doc_requirement:
            return self.api_response(
                message="Visa document requirement already exists or error creating requirement.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Visa document requirement created successfully.",
            data=VisaDocumentRequirementSerializer(doc_requirement).data,
            status_code=status.HTTP_201_CREATED
        )

