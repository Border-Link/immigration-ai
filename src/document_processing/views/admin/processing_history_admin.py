"""
Admin API Views for ProcessingHistory Management

Admin-only endpoints for managing processing history.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from document_processing.services.processing_history_service import ProcessingHistoryService
from document_processing.serializers.processing_history.admin import (
    ProcessingHistoryAdminListSerializer,
    ProcessingHistoryAdminDetailSerializer,
    BulkProcessingHistoryOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
        case_document_id = request.query_params.get('case_document_id', None)
        processing_job_id = request.query_params.get('processing_job_id', None)
        action = request.query_params.get('action', None)
        status_filter = request.query_params.get('status', None)
        error_type = request.query_params.get('error_type', None)
        user_id = request.query_params.get('user_id', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        limit = request.query_params.get('limit', None)
        
        try:
            # Parse parameters
            parsed_date_from = parse_datetime(date_from) if date_from else None
            parsed_date_to = parse_datetime(date_to) if date_to else None
            limit_int = int(limit) if limit else None
            
            # Use service method with filters
            history = ProcessingHistoryService.get_by_filters(
                case_document_id=case_document_id,
                processing_job_id=processing_job_id,
                action=action,
                status=status_filter,
                error_type=error_type,
                user_id=user_id,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                limit=limit_int
            )
            
            return self.api_response(
                message="Processing history retrieved successfully.",
                data=ProcessingHistoryAdminListSerializer(history, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving processing history: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving processing history.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingHistoryAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed processing history entry.
    
    Endpoint: GET /api/v1/document-processing/admin/processing-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            history = ProcessingHistoryService.get_by_id(id)
            if not history:
                return self.api_response(
                    message=f"Processing history entry with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Processing history retrieved successfully.",
                data=ProcessingHistoryAdminDetailSerializer(history).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving processing history {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving processing history.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingHistoryAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a processing history entry.
    
    Endpoint: DELETE /api/v1/document-processing/admin/processing-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            success = ProcessingHistoryService.delete_history_entry(id)
            if not success:
                return self.api_response(
                    message=f"Processing history entry with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Processing history entry deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting processing history {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting processing history entry.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkProcessingHistoryOperationAPI(AuthAPI):
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
    
    def post(self, request):
        serializer = BulkProcessingHistoryOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        history_ids = serializer.validated_data['history_ids']
        operation = serializer.validated_data['operation']
        
        try:
            if operation == 'delete':
                deleted_count = 0
                failed_count = 0
                
                for history_id in history_ids:
                    success = ProcessingHistoryService.delete_history_entry(str(history_id))
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Deleted: {deleted_count}, Failed: {failed_count}.",
                    data={
                        'deleted_count': deleted_count,
                        'failed_count': failed_count,
                        'total_requested': len(history_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Unknown operation: {operation}",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error performing bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
