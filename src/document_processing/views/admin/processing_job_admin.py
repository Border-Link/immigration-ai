"""
Admin API Views for ProcessingJob Management

Admin-only endpoints for managing processing jobs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.serializers.processing_job.admin import (
    ProcessingJobAdminListQuerySerializer,
    ProcessingJobAdminListSerializer,
    ProcessingJobAdminDetailSerializer,
    ProcessingJobAdminUpdateSerializer,
    BulkProcessingJobOperationSerializer,
)


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
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = ProcessingJobAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        jobs = ProcessingJobService.get_by_filters(
            case_document_id=str(query_serializer.validated_data.get('case_document_id')) if query_serializer.validated_data.get('case_document_id') else None,
            status=query_serializer.validated_data.get('status'),
            processing_type=query_serializer.validated_data.get('processing_type'),
            error_type=query_serializer.validated_data.get('error_type'),
            created_by_id=str(query_serializer.validated_data.get('created_by_id')) if query_serializer.validated_data.get('created_by_id') else None,
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to'),
            min_priority=query_serializer.validated_data.get('min_priority'),
            max_retries_exceeded=query_serializer.validated_data.get('max_retries_exceeded')
        )
        
        return self.api_response(
            message="Processing jobs retrieved successfully.",
            data=ProcessingJobAdminListSerializer(jobs, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ProcessingJobAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed processing job information.
    
    Endpoint: GET /api/v1/document-processing/admin/processing-jobs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Processing job"
    
    def get_entity_by_id(self, entity_id):
        """Get processing job by ID."""
        return ProcessingJobService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return ProcessingJobAdminDetailSerializer


class ProcessingJobAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update processing job.
    
    Endpoint: PUT /api/v1/document-processing/admin/processing-jobs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Processing job"
    
    def get_entity_by_id(self, entity_id):
        """Get processing job by ID."""
        return ProcessingJobService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return ProcessingJobAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return ProcessingJobAdminDetailSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the processing job."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return ProcessingJobService.update_processing_job(str(entity.id), **update_fields)
    
    def put(self, request, id):
        """Override to support PUT method (base class uses PATCH)."""
        return self.patch(request, id)


class ProcessingJobAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a processing job.
    
    Endpoint: DELETE /api/v1/document-processing/admin/processing-jobs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Processing job"
    
    def get_entity_by_id(self, entity_id):
        """Get processing job by ID."""
        return ProcessingJobService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the processing job."""
        return ProcessingJobService.delete_processing_job(str(entity.id))


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
    permission_classes = [AdminPermission]
    
    def post(self, request):
        serializer = BulkProcessingJobOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        job_ids = serializer.validated_data['job_ids']
        operation = serializer.validated_data['operation']
        
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
