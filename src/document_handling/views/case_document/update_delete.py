from rest_framework import status
from main_system.base.auth_api import AuthAPI
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.serializers.case_document.update_delete import (
    CaseDocumentUpdateSerializer,
    CaseDocumentDeleteSerializer
)
from document_handling.serializers.case_document.read import CaseDocumentSerializer


class CaseDocumentUpdateAPI(AuthAPI):
    """Update a case document by ID."""

    def patch(self, request, id):
        serializer = CaseDocumentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Handle document_type_id separately if provided
        update_fields = {}
        if 'status' in serializer.validated_data:
            update_fields['status'] = serializer.validated_data['status']
        
        if 'document_type_id' in serializer.validated_data:
            from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector
            document_type = DocumentTypeSelector.get_by_id(serializer.validated_data['document_type_id'])
            update_fields['document_type'] = document_type

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

