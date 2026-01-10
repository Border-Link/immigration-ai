"""
Admin API Views for DocumentVersion Management

Admin-only endpoints for managing document versions.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.document_version_service import DocumentVersionService
from data_ingestion.serializers.document_version.read import DocumentVersionSerializer, DocumentVersionListSerializer
from data_ingestion.serializers.document_version.admin import BulkDocumentVersionOperationSerializer
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
        source_document_id = request.query_params.get('source_document_id', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            versions = DocumentVersionService.get_by_filters(
                source_document_id=source_document_id,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Document versions retrieved successfully.",
                data=DocumentVersionListSerializer(versions, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document versions: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document versions.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentVersionAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed document version information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            version = DocumentVersionService.get_by_id(id)
            if not version:
                return self.api_response(
                    message=f"Document version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document version retrieved successfully.",
                data=DocumentVersionSerializer(version).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document version {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentVersionAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete document version.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/document-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            version = DocumentVersionService.get_by_id(id)
            if not version:
                return self.api_response(
                    message=f"Document version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = DocumentVersionService.delete_document_version(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting document version.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Document version deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting document version {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting document version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDocumentVersionOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on document versions.
    
    Endpoint: POST /api/v1/data-ingestion/admin/document-versions/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkDocumentVersionOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        version_ids = serializer.validated_data['version_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for version_id in version_ids:
                try:
                    if operation == 'delete':
                        deleted = DocumentVersionService.delete_document_version(str(version_id))
                        if deleted:
                            results['success'].append(str(version_id))
                        else:
                            results['failed'].append({
                                'version_id': str(version_id),
                                'error': 'Document version not found or failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'version_id': str(version_id),
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
