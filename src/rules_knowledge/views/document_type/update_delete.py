from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_permission import RulePermission
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.serializers.document_type.read import DocumentTypeSerializer
from rules_knowledge.serializers.document_type.update_delete import DocumentTypeUpdateSerializer


class DocumentTypeUpdateAPI(AuthAPI):
    """Update a document type. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def patch(self, request, id):
        serializer = DocumentTypeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_type = DocumentTypeService.update_document_type(id, **serializer.validated_data)
        if not document_type:
            return self.api_response(
                message=f"Document type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document type updated successfully.",
            data=DocumentTypeSerializer(document_type).data,
            status_code=status.HTTP_200_OK
        )


class DocumentTypeDeleteAPI(AuthAPI):
    """Delete a document type. Only admin/staff can access."""
    permission_classes = [RulePermission]

    def delete(self, request, id):
        success = DocumentTypeService.delete_document_type(id)
        if not success:
            return self.api_response(
                message=f"Document type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document type deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

