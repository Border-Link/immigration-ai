from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ingestion_permission import IngestionPermission
from data_ingestion.services.document_diff_service import DocumentDiffService
from data_ingestion.serializers.document_diff.read import (
    DocumentDiffSerializer,
    DocumentDiffListSerializer
)


class DocumentDiffListAPI(AuthAPI):
    """Get all document diffs."""
    permission_classes = [IngestionPermission]

    def get(self, request):
        change_type = request.query_params.get('change_type', None)
        
        if change_type:
            document_diffs = DocumentDiffService.get_by_change_type(change_type)
        else:
            document_diffs = DocumentDiffService.get_all()

        return self.api_response(
            message="Document diffs retrieved successfully.",
            data=DocumentDiffListSerializer(document_diffs, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DocumentDiffDetailAPI(AuthAPI):
    """Get document diff by ID."""
    permission_classes = [IngestionPermission]

    def get(self, request, id):
        document_diff = DocumentDiffService.get_by_id(id)
        
        if not document_diff:
            return self.api_response(
                message=f"Document diff with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document diff retrieved successfully.",
            data=DocumentDiffSerializer(document_diff).data,
            status_code=status.HTTP_200_OK
        )

