"""
Admin API Views for DocumentDiff Management

Admin-only endpoints for managing document diffs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
)
from data_ingestion.services.document_diff_service import DocumentDiffService
from data_ingestion.serializers.document_diff.read import DocumentDiffSerializer, DocumentDiffListSerializer
from data_ingestion.serializers.document_diff.admin import (
    DocumentDiffAdminListQuerySerializer,
    BulkDocumentDiffOperationSerializer,
)


class DocumentDiffAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document diffs with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-diffs/
    Auth: Required (staff/superuser only)
    Query Params:
        - change_type: Filter by change type
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = DocumentDiffAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        diffs = DocumentDiffService.get_by_filters(
            change_type=query_serializer.validated_data.get('change_type'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Document diffs retrieved successfully.",
            data=DocumentDiffListSerializer(diffs, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DocumentDiffAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed document diff information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-diffs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document diff"
    
    def get_entity_by_id(self, entity_id):
        """Get document diff by ID."""
        return DocumentDiffService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DocumentDiffSerializer


class DocumentDiffAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete document diff.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/document-diffs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document diff"
    
    def get_entity_by_id(self, entity_id):
        """Get document diff by ID."""
        return DocumentDiffService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the document diff."""
        return DocumentDiffService.delete_document_diff(str(entity.id))


class BulkDocumentDiffOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on document diffs.
    
    Endpoint: POST /api/v1/data-ingestion/admin/document-diffs/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk document diff operation serializer."""
        return BulkDocumentDiffOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document diff"
    
    def get_entity_by_id(self, entity_id):
        """Get document diff by ID."""
        return DocumentDiffService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the document diff."""
        if operation == 'delete':
            return DocumentDiffService.delete_document_diff(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
