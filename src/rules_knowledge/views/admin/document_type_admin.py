"""
Admin API Views for DocumentType Management

Admin-only endpoints for managing document types.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.serializers.document_type.read import DocumentTypeSerializer, DocumentTypeListSerializer
from rules_knowledge.serializers.document_type.admin import (
    DocumentTypeActivateSerializer,
    BulkDocumentTypeOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        is_active = request.query_params.get('is_active', None)
        code = request.query_params.get('code', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            is_active_bool = is_active.lower() == 'true' if is_active is not None else None
            
            # Use service method with filters
            document_types = DocumentTypeService.get_by_filters(
                is_active=is_active_bool,
                code=code,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Document types retrieved successfully.",
                data=DocumentTypeListSerializer(document_types, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document types: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document types.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentTypeAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed document type information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/document-types/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            document_type = DocumentTypeService.get_by_id(id)
            if not document_type:
                return self.api_response(
                    message=f"Document type with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document type retrieved successfully.",
                data=DocumentTypeSerializer(document_type).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document type {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentTypeAdminActivateAPI(AuthAPI):
    """
    Admin: Activate or deactivate a document type.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/document-types/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = DocumentTypeActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            document_type = DocumentTypeService.get_by_id(id)
            if not document_type:
                return self.api_response(
                    message=f"Document type with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_document_type = DocumentTypeService.activate_document_type(
                document_type,
                serializer.validated_data['is_active']
            )
            
            action = "activated" if serializer.validated_data['is_active'] else "deactivated"
            return self.api_response(
                message=f"Document type {action} successfully.",
                data=DocumentTypeSerializer(updated_document_type).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error activating/deactivating document type {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error activating/deactivating document type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentTypeAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete document type.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/document-types/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            document_type = DocumentTypeService.get_by_id(id)
            if not document_type:
                return self.api_response(
                    message=f"Document type with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = DocumentTypeService.delete_document_type(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting document type.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Document type deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting document type {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting document type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDocumentTypeOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on document types.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/document-types/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkDocumentTypeOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document_type_ids = serializer.validated_data['document_type_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for document_type_id in document_type_ids:
                try:
                    document_type = DocumentTypeService.get_by_id(str(document_type_id))
                    if not document_type:
                        results['failed'].append({
                            'document_type_id': str(document_type_id),
                            'error': 'Document type not found'
                        })
                        continue
                    
                    if operation == 'activate':
                        DocumentTypeService.activate_document_type(document_type, True)
                        results['success'].append(str(document_type_id))
                    elif operation == 'deactivate':
                        DocumentTypeService.activate_document_type(document_type, False)
                        results['success'].append(str(document_type_id))
                    elif operation == 'delete':
                        deleted = DocumentTypeService.delete_document_type(str(document_type_id))
                        if deleted:
                            results['success'].append(str(document_type_id))
                        else:
                            results['failed'].append({
                                'document_type_id': str(document_type_id),
                                'error': 'Failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'document_type_id': str(document_type_id),
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
