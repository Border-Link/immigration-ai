"""
Admin API Views for DocumentVersion Management

Admin-only endpoints for managing document versions.
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
from data_ingestion.services.document_version_service import DocumentVersionService
from data_ingestion.serializers.document_version.read import DocumentVersionSerializer, DocumentVersionListSerializer
from data_ingestion.serializers.document_version.admin import (
    DocumentVersionAdminListQuerySerializer,
    BulkDocumentVersionOperationSerializer,
)


class DocumentVersionAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document versions with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-versions/
    Auth: Required (staff/superuser only)
    Query Params:
        - source_document_id: Filter by source document ID
        - date_from: Filter by extracted date (from)
        - date_to: Filter by extracted date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = DocumentVersionAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        versions = DocumentVersionService.get_by_filters(
            source_document_id=str(query_serializer.validated_data.get('source_document_id')) if query_serializer.validated_data.get('source_document_id') else None,
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Document versions retrieved successfully.",
            data=DocumentVersionListSerializer(versions, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DocumentVersionAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed document version information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document version"
    
    def get_entity_by_id(self, entity_id):
        """Get document version by ID."""
        return DocumentVersionService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DocumentVersionSerializer


class DocumentVersionAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete document version.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/document-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document version"
    
    def get_entity_by_id(self, entity_id):
        """Get document version by ID."""
        return DocumentVersionService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the document version."""
        return DocumentVersionService.delete_document_version(str(entity.id))


class BulkDocumentVersionOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on document versions.
    
    Endpoint: POST /api/v1/data-ingestion/admin/document-versions/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk document version operation serializer."""
        return BulkDocumentVersionOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document version"
    
    def get_entity_by_id(self, entity_id):
        """Get document version by ID."""
        return DocumentVersionService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the document version."""
        if operation == 'delete':
            return DocumentVersionService.delete_document_version(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
