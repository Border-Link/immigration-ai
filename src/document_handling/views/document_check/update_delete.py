from rest_framework import status
from main_system.base.auth_api import AuthAPI
from document_handling.services.document_check_service import DocumentCheckService
from document_handling.serializers.document_check.update_delete import (
    DocumentCheckUpdateSerializer,
    DocumentCheckDeleteSerializer
)
from document_handling.serializers.document_check.read import DocumentCheckSerializer


class DocumentCheckUpdateAPI(AuthAPI):
    """Update a document check by ID."""

    def patch(self, request, id):
        serializer = DocumentCheckUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_check = DocumentCheckService.update_document_check(id, **serializer.validated_data)

        if not document_check:
            return self.api_response(
                message=f"Document check with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document check updated successfully.",
            data=DocumentCheckSerializer(document_check).data,
            status_code=status.HTTP_200_OK
        )


class DocumentCheckDeleteAPI(AuthAPI):
    """Delete a document check by ID."""

    def delete(self, request, id):
        success = DocumentCheckService.delete_document_check(id)

        if not success:
            return self.api_response(
                message=f"Document check with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document check deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

