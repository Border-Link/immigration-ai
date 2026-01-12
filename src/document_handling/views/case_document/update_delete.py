from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.document_permission import DocumentPermission
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.serializers.case_document.update_delete import (
    CaseDocumentUpdateSerializer,
    CaseDocumentDeleteSerializer
)
from document_handling.serializers.case_document.read import CaseDocumentSerializer


class CaseDocumentUpdateAPI(AuthAPI):
    """Update a case document by ID."""
    permission_classes = [DocumentPermission]

    def patch(self, request, id):
        serializer = CaseDocumentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract update fields - service will handle document_type_id conversion
        update_fields = serializer.validated_data.copy()

        case_document = CaseDocumentService.update_case_document(id, **update_fields)

        if not case_document:
            return self.api_response(
                message=f"Case document with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case document updated successfully.",
            data=CaseDocumentSerializer(case_document).data,
            status_code=status.HTTP_200_OK
        )


class CaseDocumentDeleteAPI(AuthAPI):
    """Delete a case document by ID."""
    permission_classes = [DocumentPermission]

    def delete(self, request, id):
        success = CaseDocumentService.delete_case_document(id)

        if not success:
            return self.api_response(
                message=f"Case document with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case document deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

