"""
Admin API Views for DocumentDiff Management

Admin-only endpoints for managing document diffs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.document_diff_service import DocumentDiffService
from data_ingestion.serializers.document_diff.read import DocumentDiffSerializer, DocumentDiffListSerializer
from data_ingestion.serializers.document_diff.admin import BulkDocumentDiffOperationSerializer
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        change_type = request.query_params.get('change_type', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            diffs = DocumentDiffService.get_by_filters(
                change_type=change_type,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Document diffs retrieved successfully.",
                data=DocumentDiffListSerializer(diffs, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document diffs: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document diffs.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDiffAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed document diff information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-diffs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            diff = DocumentDiffService.get_by_id(id)
            if not diff:
                return self.api_response(
                    message=f"Document diff with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document diff retrieved successfully.",
                data=DocumentDiffSerializer(diff).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document diff {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document diff.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDiffAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete document diff.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/document-diffs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            deleted = DocumentDiffService.delete_document_diff(id)
            if not deleted:
                return self.api_response(
                    message=f"Document diff with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document diff deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting document diff {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting document diff.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDocumentDiffOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on document diffs.
    
    Endpoint: POST /api/v1/data-ingestion/admin/document-diffs/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkDocumentDiffOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        diff_ids = serializer.validated_data['diff_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for diff_id in diff_ids:
                try:
                    if operation == 'delete':
                        deleted = DocumentDiffService.delete_document_diff(str(diff_id))
                        if deleted:
                            results['success'].append(str(diff_id))
                        else:
                            results['failed'].append({
                                'diff_id': str(diff_id),
                                'error': 'Document diff not found or failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'diff_id': str(diff_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
