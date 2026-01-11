"""
Admin API Views for DocumentCheck Management

Admin-only endpoints for managing document checks.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from document_handling.services.document_check_service import DocumentCheckService
from document_handling.serializers.document_check.admin import (
    DocumentCheckAdminListQuerySerializer,
    DocumentCheckAdminListSerializer,
    DocumentCheckAdminDetailSerializer,
    DocumentCheckAdminUpdateSerializer,
    BulkDocumentCheckOperationSerializer,
)


class DocumentCheckAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document checks with advanced filtering.
    
    Endpoint: GET /api/v1/document-handling/admin/document-checks/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_document_id: Filter by case document ID
        - check_type: Filter by check type (ocr, classification, validation, authenticity)
        - result: Filter by result (passed, failed, warning, pending)
        - performed_by: Filter by who performed the check
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = DocumentCheckAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        checks = DocumentCheckService.get_by_filters(
            case_document_id=str(query_serializer.validated_data.get('case_document_id')) if query_serializer.validated_data.get('case_document_id') else None,
            check_type=query_serializer.validated_data.get('check_type'),
            result=query_serializer.validated_data.get('result'),
            performed_by=query_serializer.validated_data.get('performed_by'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Document checks retrieved successfully.",
            data=DocumentCheckAdminListSerializer(checks, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DocumentCheckAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed document check information.
    
    Endpoint: GET /api/v1/document-handling/admin/document-checks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document check"
    
    def get_entity_by_id(self, entity_id):
        """Get document check by ID."""
        return DocumentCheckService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DocumentCheckAdminDetailSerializer


class DocumentCheckAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update document check.
    
    Endpoint: PUT /api/v1/document-handling/admin/document-checks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document check"
    
    def get_entity_by_id(self, entity_id):
        """Get document check by ID."""
        return DocumentCheckService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return DocumentCheckAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return DocumentCheckAdminDetailSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the document check."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return DocumentCheckService.update_document_check(str(entity.id), **update_fields)
    
    def put(self, request, id):
        """Override to support PUT method (base class uses PATCH)."""
        return self.patch(request, id)


class DocumentCheckAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a document check.
    
    Endpoint: DELETE /api/v1/document-handling/admin/document-checks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document check"
    
    def get_entity_by_id(self, entity_id):
        """Get document check by ID."""
        return DocumentCheckService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the document check."""
        return DocumentCheckService.delete_document_check(str(entity.id))


class BulkDocumentCheckOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on document checks.
    
    Endpoint: POST /api/v1/document-handling/admin/document-checks/bulk-operation/
    Auth: Required (staff/superuser only)
    Body:
        {
            "check_ids": ["uuid1", "uuid2", ...],
            "operation": "delete"
        }
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk document check operation serializer."""
        return BulkDocumentCheckOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document check"
    
    def get_entity_by_id(self, entity_id):
        """Get document check by ID."""
        return DocumentCheckService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the document check."""
        if operation == 'delete':
            return DocumentCheckService.delete_document_check(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
