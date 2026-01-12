"""
Admin API Views for DocumentType Management

Admin-only endpoints for managing document types.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminActivateAPI,
)
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.serializers.document_type.read import DocumentTypeSerializer, DocumentTypeListSerializer
from rules_knowledge.serializers.document_type.admin import (
    DocumentTypeAdminListQuerySerializer,
    DocumentTypeActivateSerializer,
    BulkDocumentTypeOperationSerializer,
)


class DocumentTypeAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document types with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/document-types/
    Auth: Required (staff/superuser only)
    Query Params:
        - is_active: Filter by active status
        - code: Filter by code (partial match)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = DocumentTypeAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        document_types = DocumentTypeService.get_by_filters(
            is_active=validated_params.get('is_active'),
            code=validated_params.get('code'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        from main_system.utils import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(document_types, page=page, page_size=page_size)
        
        return self.api_response(
            message="Document types retrieved successfully.",
            data={
                'items': DocumentTypeListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class DocumentTypeAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed document type information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/document-types/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document type"
    
    def get_entity_by_id(self, entity_id):
        """Get document type by ID."""
        return DocumentTypeService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DocumentTypeSerializer


class DocumentTypeAdminActivateAPI(BaseAdminActivateAPI):
    """
    Admin: Activate or deactivate a document type.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/document-types/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document type"
    
    def get_entity_by_id(self, entity_id):
        """Get document type by ID."""
        return DocumentTypeService.get_by_id(entity_id)
    
    def activate_entity(self, entity, is_active):
        """Activate or deactivate the document type."""
        updated = DocumentTypeService.activate_document_type(entity, is_active)
        return updated is not None
    
    def post(self, request, id):
        """Override to return serialized data in response."""
        from main_system.serializers.admin.base import ActivateSerializer
        
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_active = serializer.validated_data['is_active']
        
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            updated = DocumentTypeService.activate_document_type(entity, is_active)
            if updated:
                action = "activated" if is_active else "deactivated"
                return self.api_response(
                    message=f"{self.get_entity_name()} {action} successfully.",
                    data=DocumentTypeSerializer(updated).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to update {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Error updating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentTypeAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete document type.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/document-types/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document type"
    
    def get_entity_by_id(self, entity_id):
        """Get document type by ID."""
        return DocumentTypeService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the document type."""
        return DocumentTypeService.delete_document_type(str(entity.id))


class BulkDocumentTypeOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on document types.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/document-types/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk document type operation serializer."""
        return BulkDocumentTypeOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document type"
    
    def get_entity_by_id(self, entity_id):
        """Get document type by ID."""
        return DocumentTypeService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the document type."""
        if operation == 'activate':
            DocumentTypeService.activate_document_type(entity, True)
            return entity
        elif operation == 'deactivate':
            DocumentTypeService.activate_document_type(entity, False)
            return entity
        elif operation == 'delete':
            return DocumentTypeService.delete_document_type(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
