from rest_framework import status
from main_system.base.auth_api import AuthAPI
from data_ingestion.services.source_document_service import SourceDocumentService
from data_ingestion.serializers.source_document.read import (
    SourceDocumentSerializer,
    SourceDocumentListSerializer
)


class SourceDocumentListAPI(AuthAPI):
    """Get all source documents."""

    def get(self, request):
        data_source_id = request.query_params.get('data_source_id', None)
        
        if data_source_id:
            source_documents = SourceDocumentService.get_by_data_source(data_source_id)
        else:
            source_documents = SourceDocumentService.get_all()

        return self.api_response(
            message="Source documents retrieved successfully.",
            data=SourceDocumentListSerializer(source_documents, many=True).data,
            status_code=status.HTTP_200_OK
        )


class SourceDocumentDetailAPI(AuthAPI):
    """Get source document by ID."""

    def get(self, request, id):
        source_document = SourceDocumentService.get_by_id(id)
        
        if not source_document:
            return self.api_response(
                message=f"Source document with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Source document retrieved successfully.",
            data=SourceDocumentSerializer(source_document).data,
            status_code=status.HTTP_200_OK
        )


class SourceDocumentLatestAPI(AuthAPI):
    """Get latest source document for a data source."""

    def get(self, request, data_source_id):
        source_document = SourceDocumentService.get_latest_by_data_source(data_source_id)
        
        if not source_document:
            return self.api_response(
                message=f"No source documents found for data source '{data_source_id}'.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Latest source document retrieved successfully.",
            data=SourceDocumentSerializer(source_document).data,
            status_code=status.HTTP_200_OK
        )

