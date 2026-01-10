"""
Admin API Views for SourceDocument Management

Admin-only endpoints for managing source documents.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.source_document_service import SourceDocumentService
from data_ingestion.serializers.source_document.read import SourceDocumentSerializer, SourceDocumentListSerializer
from data_ingestion.serializers.source_document.admin import BulkSourceDocumentOperationSerializer
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
        data_source_id = request.query_params.get('data_source_id', None)
        has_error = request.query_params.get('has_error', None)
        http_status = request.query_params.get('http_status', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse parameters
            has_error_bool = has_error.lower() == 'true' if has_error is not None else None
            http_status_int = int(http_status) if http_status else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            documents = SourceDocumentService.get_by_filters(
                data_source_id=data_source_id,
                has_error=has_error_bool,
                http_status=http_status_int,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Source documents retrieved successfully.",
                data=SourceDocumentListSerializer(documents, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving source documents: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving source documents.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SourceDocumentAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed source document information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/source-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            document = SourceDocumentService.get_by_id(id)
            if not document:
                return self.api_response(
                    message=f"Source document with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Source document retrieved successfully.",
                data=SourceDocumentSerializer(document).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving source document {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving source document.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SourceDocumentAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete source document.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/source-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            document = SourceDocumentService.get_by_id(id)
            if not document:
                return self.api_response(
                    message=f"Source document with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = SourceDocumentService.delete_source_document(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting source document.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Source document deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting source document {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting source document.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkSourceDocumentOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on source documents.
    
    Endpoint: POST /api/v1/data-ingestion/admin/source-documents/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkSourceDocumentOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document_ids = serializer.validated_data['document_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for document_id in document_ids:
                try:
                    if operation == 'delete':
                        deleted = SourceDocumentService.delete_source_document(str(document_id))
                        if deleted:
                            results['success'].append(str(document_id))
                        else:
                            results['failed'].append({
                                'document_id': str(document_id),
                                'error': 'Source document not found or failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'document_id': str(document_id),
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
