"""
Admin API Views for ProcessingJob Management

Admin-only endpoints for managing processing jobs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.serializers.processing_job.admin import (
    ProcessingJobAdminListSerializer,
    ProcessingJobAdminDetailSerializer,
    ProcessingJobAdminUpdateSerializer,
    BulkProcessingJobOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class ProcessingJobAdminListAPI(AuthAPI):
    """
    Admin: Get list of all processing jobs with advanced filtering.
    
    Endpoint: GET /api/v1/document-processing/admin/processing-jobs/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_document_id: Filter by case document ID
        - status: Filter by status (pending, queued, processing, completed, failed, cancelled)
        - processing_type: Filter by processing type (ocr, classification, validation, full, reprocess)
        - error_type: Filter by error type
        - created_by_id: Filter by creator ID
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - min_priority: Filter by minimum priority
        - max_retries_exceeded: Filter by retry count exceeded (true/false)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        case_document_id = request.query_params.get('case_document_id', None)
        status_filter = request.query_params.get('status', None)
        processing_type = request.query_params.get('processing_type', None)
        error_type = request.query_params.get('error_type', None)
        created_by_id = request.query_params.get('created_by_id', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        min_priority = request.query_params.get('min_priority', None)
        max_retries_exceeded = request.query_params.get('max_retries_exceeded', None)
        
        try:
            # Parse parameters
            parsed_date_from = parse_datetime(date_from) if date_from else None
            parsed_date_to = parse_datetime(date_to) if date_to else None
            min_priority_int = int(min_priority) if min_priority else None
            max_retries_exceeded_bool = max_retries_exceeded.lower() == 'true' if max_retries_exceeded is not None else None
            
            # Use service method with filters
            jobs = ProcessingJobService.get_by_filters(
                case_document_id=case_document_id,
                status=status_filter,
                processing_type=processing_type,
                error_type=error_type,
                created_by_id=created_by_id,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                min_priority=min_priority_int,
                max_retries_exceeded=max_retries_exceeded_bool
            )
            
            return self.api_response(
                message="Processing jobs retrieved successfully.",
                data=ProcessingJobAdminListSerializer(jobs, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving processing jobs: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving processing jobs.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingJobAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed processing job information.
    
    Endpoint: GET /api/v1/document-processing/admin/processing-jobs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            job = ProcessingJobService.get_by_id(id)
            if not job:
                return self.api_response(
                    message=f"Processing job with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Processing job retrieved successfully.",
                data=ProcessingJobAdminDetailSerializer(job).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving processing job {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving processing job.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingJobAdminUpdateAPI(AuthAPI):
    """
    Admin: Update processing job.
    
    Endpoint: PUT /api/v1/document-processing/admin/processing-jobs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def put(self, request, id):
        serializer = ProcessingJobAdminUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            update_fields = {}
            if 'status' in serializer.validated_data:
                update_fields['status'] = serializer.validated_data['status']
            if 'priority' in serializer.validated_data:
                update_fields['priority'] = serializer.validated_data['priority']
            if 'max_retries' in serializer.validated_data:
                update_fields['max_retries'] = serializer.validated_data['max_retries']
            if 'error_message' in serializer.validated_data:
                update_fields['error_message'] = serializer.validated_data['error_message']
            if 'error_type' in serializer.validated_data:
                update_fields['error_type'] = serializer.validated_data['error_type']
            if 'metadata' in serializer.validated_data:
                update_fields['metadata'] = serializer.validated_data['metadata']
            
            updated_job = ProcessingJobService.update_processing_job(id, **update_fields)
            if not updated_job:
                return self.api_response(
                    message=f"Processing job with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Processing job updated successfully.",
                data=ProcessingJobAdminDetailSerializer(updated_job).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating processing job {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating processing job.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingJobAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a processing job.
    
    Endpoint: DELETE /api/v1/document-processing/admin/processing-jobs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            success = ProcessingJobService.delete_processing_job(id)
            if not success:
                return self.api_response(
                    message=f"Processing job with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Processing job deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting processing job {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting processing job.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkProcessingJobOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on processing jobs.
    
    Endpoint: POST /api/v1/document-processing/admin/processing-jobs/bulk-operation/
    Auth: Required (staff/superuser only)
    Body:
        {
            "job_ids": ["uuid1", "uuid2", ...],
            "operation": "delete" | "cancel" | "retry" | "update_status" | "update_priority",
            "status": "cancelled" (required if operation is update_status),
            "priority": 8 (required if operation is update_priority)
        }
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkProcessingJobOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        job_ids = serializer.validated_data['job_ids']
        operation = serializer.validated_data['operation']
        
        try:
            if operation == 'delete':
                deleted_count = 0
                failed_count = 0
                
                for job_id in job_ids:
                    success = ProcessingJobService.delete_processing_job(str(job_id))
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Deleted: {deleted_count}, Failed: {failed_count}.",
                    data={
                        'deleted_count': deleted_count,
                        'failed_count': failed_count,
                        'total_requested': len(job_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'cancel':
                cancelled_count = 0
                failed_count = 0
                
                for job_id in job_ids:
                    updated = ProcessingJobService.update_status(str(job_id), 'cancelled')
                    if updated:
                        cancelled_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Cancelled: {cancelled_count}, Failed: {failed_count}.",
                    data={
                        'cancelled_count': cancelled_count,
                        'failed_count': failed_count,
                        'total_requested': len(job_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'retry':
                # Reset failed jobs to pending for retry
                retried_count = 0
                failed_count = 0
                
                for job_id in job_ids:
                    job = ProcessingJobService.get_by_id(str(job_id))
                    if job and job.status == 'failed' and job.retry_count < job.max_retries:
                        updated = ProcessingJobService.update_processing_job(
                            str(job_id),
                            status='pending',
                            retry_count=0,
                            error_message=None,
                            error_type=None
                        )
                        if updated:
                            retried_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Retried: {retried_count}, Failed: {failed_count}.",
                    data={
                        'retried_count': retried_count,
                        'failed_count': failed_count,
                        'total_requested': len(job_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'update_status':
                status_value = serializer.validated_data.get('status')
                if not status_value:
                    return self.api_response(
                        message="Status is required for update_status operation.",
                        data=None,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                updated_count = 0
                failed_count = 0
                
                for job_id in job_ids:
                    updated = ProcessingJobService.update_status(str(job_id), status_value)
                    if updated:
                        updated_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Updated: {updated_count}, Failed: {failed_count}.",
                    data={
                        'updated_count': updated_count,
                        'failed_count': failed_count,
                        'total_requested': len(job_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'update_priority':
                priority_value = serializer.validated_data.get('priority')
                if priority_value is None:
                    return self.api_response(
                        message="Priority is required for update_priority operation.",
                        data=None,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                updated_count = 0
                failed_count = 0
                
                for job_id in job_ids:
                    updated = ProcessingJobService.update_processing_job(str(job_id), priority=priority_value)
                    if updated:
                        updated_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Updated: {updated_count}, Failed: {failed_count}.",
                    data={
                        'updated_count': updated_count,
                        'failed_count': failed_count,
                        'total_requested': len(job_ids),
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
