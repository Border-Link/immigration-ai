"""
Admin API Views for ProcessingHistory Management

Admin-only endpoints for managing processing history.
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
from document_processing.services.processing_history_service import ProcessingHistoryService
from document_processing.serializers.processing_history.admin import (
    ProcessingHistoryAdminListQuerySerializer,
    ProcessingHistoryAdminListSerializer,
    ProcessingHistoryAdminDetailSerializer,
    BulkProcessingHistoryOperationSerializer,
)


class ProcessingHistoryAdminListAPI(AuthAPI):
    """
    Admin: Get list of all processing history entries with advanced filtering.
    
    Endpoint: GET /api/v1/document-processing/admin/processing-history/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_document_id: Filter by case document ID
        - processing_job_id: Filter by processing job ID
        - action: Filter by action type
        - status: Filter by status (success, failure, warning)
        - error_type: Filter by error type
        - user_id: Filter by user ID
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - limit: Limit number of results
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = ProcessingHistoryAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        history = ProcessingHistoryService.get_by_filters(
            case_document_id=str(query_serializer.validated_data.get('case_document_id')) if query_serializer.validated_data.get('case_document_id') else None,
            processing_job_id=str(query_serializer.validated_data.get('processing_job_id')) if query_serializer.validated_data.get('processing_job_id') else None,
            action=query_serializer.validated_data.get('action'),
            status=query_serializer.validated_data.get('status'),
            error_type=query_serializer.validated_data.get('error_type'),
            user_id=str(query_serializer.validated_data.get('user_id')) if query_serializer.validated_data.get('user_id') else None,
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to'),
            limit=query_serializer.validated_data.get('limit')
        )
        
        return self.api_response(
            message="Processing history retrieved successfully.",
            data=ProcessingHistoryAdminListSerializer(history, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ProcessingHistoryAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed processing history entry.
    
    Endpoint: GET /api/v1/document-processing/admin/processing-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Processing history entry"
    
    def get_entity_by_id(self, entity_id):
        """Get processing history entry by ID."""
        return ProcessingHistoryService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return ProcessingHistoryAdminDetailSerializer


class ProcessingHistoryAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a processing history entry.
    
    Endpoint: DELETE /api/v1/document-processing/admin/processing-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Processing history entry"
    
    def get_entity_by_id(self, entity_id):
        """Get processing history entry by ID."""
        return ProcessingHistoryService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the processing history entry."""
        return ProcessingHistoryService.delete_history_entry(str(entity.id))


class BulkProcessingHistoryOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on processing history.
    
    Endpoint: POST /api/v1/document-processing/admin/processing-history/bulk-operation/
    Auth: Required (staff/superuser only)
    Body:
        {
            "history_ids": ["uuid1", "uuid2", ...],
            "operation": "delete"
        }
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk processing history operation serializer."""
        return BulkProcessingHistoryOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Processing history entry"
    
    def get_entity_by_id(self, entity_id):
        """Get processing history entry by ID."""
        return ProcessingHistoryService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the processing history entry."""
        if operation == 'delete':
            return ProcessingHistoryService.delete_history_entry(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
