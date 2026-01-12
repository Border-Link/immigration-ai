from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ingestion_permission import IngestionPermission
from data_ingestion.services.document_version_service import DocumentVersionService
from data_ingestion.serializers.document_version.read import (
    DocumentVersionSerializer,
    DocumentVersionListSerializer
)


class DocumentVersionListAPI(AuthAPI):
    """Get all document versions."""
    permission_classes = [IngestionPermission]

    def get(self, request):
        source_document_id = request.query_params.get('source_document_id', None)
        
        if source_document_id:
            document_versions = DocumentVersionService.get_by_source_document(source_document_id)
        else:
            document_versions = DocumentVersionService.get_all()

        return self.api_response(
            message="Document versions retrieved successfully.",
            data=DocumentVersionListSerializer(document_versions, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DocumentVersionDetailAPI(AuthAPI):
    """Get document version by ID."""
    permission_classes = [IngestionPermission]

    def get(self, request, id):
        document_version = DocumentVersionService.get_by_id(id)
        
        if not document_version:
            return self.api_response(
                message=f"Document version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document version retrieved successfully.",
            data=DocumentVersionSerializer(document_version).data,
            status_code=status.HTTP_200_OK
        )


class DocumentVersionLatestAPI(AuthAPI):
    """Get latest document version for a source document."""
    permission_classes = [IngestionPermission]

    def get(self, request, source_document_id):
        document_version = DocumentVersionService.get_latest_by_source_document(source_document_id)
        
        if not document_version:
            return self.api_response(
                message=f"No document versions found for source document '{source_document_id}'.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Latest document version retrieved successfully.",
            data=DocumentVersionSerializer(document_version).data,
            status_code=status.HTTP_200_OK
        )

