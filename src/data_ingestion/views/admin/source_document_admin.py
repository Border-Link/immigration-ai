"""
Admin API Views for SourceDocument Management

Admin-only endpoints for managing source documents.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
)
from data_ingestion.services.source_document_service import SourceDocumentService
from data_ingestion.serializers.source_document.read import SourceDocumentSerializer, SourceDocumentListSerializer
from data_ingestion.serializers.source_document.admin import (
    SourceDocumentAdminListQuerySerializer,
    BulkSourceDocumentOperationSerializer,
)


class SourceDocumentAdminListAPI(AuthAPI):
    """
    Admin: Get list of all source documents with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/source-documents/
    Auth: Required (staff/superuser only)
    Query Params:
        - data_source_id: Filter by data source ID
        - has_error: Filter by documents with errors
        - http_status: Filter by HTTP status code
        - date_from: Filter by fetched date (from)
        - date_to: Filter by fetched date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = SourceDocumentAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        documents = SourceDocumentService.get_by_filters(
            data_source_id=str(query_serializer.validated_data.get('data_source_id')) if query_serializer.validated_data.get('data_source_id') else None,
            has_error=query_serializer.validated_data.get('has_error'),
            http_status=query_serializer.validated_data.get('http_status'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Source documents retrieved successfully.",
            data=SourceDocumentListSerializer(documents, many=True).data,
            status_code=status.HTTP_200_OK
        )


class SourceDocumentAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed source document information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/source-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Source document"
    
    def get_entity_by_id(self, entity_id):
        """Get source document by ID."""
        return SourceDocumentService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return SourceDocumentSerializer


class SourceDocumentAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete source document.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/source-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Source document"
    
    def get_entity_by_id(self, entity_id):
        """Get source document by ID."""
        return SourceDocumentService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the source document."""
        return SourceDocumentService.delete_source_document(str(entity.id))


class BulkSourceDocumentOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on source documents.
    
    Endpoint: POST /api/v1/data-ingestion/admin/source-documents/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk source document operation serializer."""
        return BulkSourceDocumentOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Source document"
    
    def get_entity_by_id(self, entity_id):
        """Get source document by ID."""
        return SourceDocumentService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the source document."""
        if operation == 'delete':
            return SourceDocumentService.delete_source_document(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
