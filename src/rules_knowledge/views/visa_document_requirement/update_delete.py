from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.serializers.visa_document_requirement.read import VisaDocumentRequirementSerializer
from rules_knowledge.serializers.visa_document_requirement.update_delete import VisaDocumentRequirementUpdateSerializer


class VisaDocumentRequirementUpdateAPI(AuthAPI):
    """Update a visa document requirement. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def patch(self, request, id):
        serializer = VisaDocumentRequirementUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_requirement = VisaDocumentRequirementService.update_visa_document_requirement(
            id, **serializer.validated_data
        )
        if not doc_requirement:
            return self.api_response(
                message=f"Visa document requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa document requirement updated successfully.",
            data=VisaDocumentRequirementSerializer(doc_requirement).data,
            status_code=status.HTTP_200_OK
        )


class VisaDocumentRequirementDeleteAPI(AuthAPI):
    """Delete a visa document requirement. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def delete(self, request, id):
        success = VisaDocumentRequirementService.delete_visa_document_requirement(id)
        if not success:
            return self.api_response(
                message=f"Visa document requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa document requirement deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

