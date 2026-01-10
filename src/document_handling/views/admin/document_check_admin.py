"""
Admin API Views for DocumentCheck Management

Admin-only endpoints for managing document checks.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from document_handling.services.document_check_service import DocumentCheckService
from document_handling.serializers.document_check.admin import (
    DocumentCheckAdminListSerializer,
    DocumentCheckAdminDetailSerializer,
    DocumentCheckAdminUpdateSerializer,
    BulkDocumentCheckOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
        case_document_id = request.query_params.get('case_document_id', None)
        check_type = request.query_params.get('check_type', None)
        result = request.query_params.get('result', None)
        performed_by = request.query_params.get('performed_by', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from else None
            parsed_date_to = parse_datetime(date_to) if date_to else None
            
            # Use service method with filters
            checks = DocumentCheckService.get_by_filters(
                case_document_id=case_document_id,
                check_type=check_type,
                result=result,
                performed_by=performed_by,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Document checks retrieved successfully.",
                data=DocumentCheckAdminListSerializer(checks, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document checks: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document checks.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentCheckAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed document check information.
    
    Endpoint: GET /api/v1/document-handling/admin/document-checks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            check = DocumentCheckService.get_by_id(id)
            if not check:
                return self.api_response(
                    message=f"Document check with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document check retrieved successfully.",
                data=DocumentCheckAdminDetailSerializer(check).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document check {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document check.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentCheckAdminUpdateAPI(AuthAPI):
    """
    Admin: Update document check.
    
    Endpoint: PUT /api/v1/document-handling/admin/document-checks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def put(self, request, id):
        serializer = DocumentCheckAdminUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            update_fields = {}
            if 'result' in serializer.validated_data:
                update_fields['result'] = serializer.validated_data['result']
            if 'details' in serializer.validated_data:
                update_fields['details'] = serializer.validated_data['details']
            if 'performed_by' in serializer.validated_data:
                update_fields['performed_by'] = serializer.validated_data['performed_by']
            
            updated_check = DocumentCheckService.update_document_check(id, **update_fields)
            if not updated_check:
                return self.api_response(
                    message=f"Document check with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document check updated successfully.",
                data=DocumentCheckAdminDetailSerializer(updated_check).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating document check {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating document check.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentCheckAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a document check.
    
    Endpoint: DELETE /api/v1/document-handling/admin/document-checks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            success = DocumentCheckService.delete_document_check(id)
            if not success:
                return self.api_response(
                    message=f"Document check with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document check deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting document check {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting document check.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDocumentCheckOperationAPI(AuthAPI):
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
    
    def post(self, request):
        serializer = BulkDocumentCheckOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        check_ids = serializer.validated_data['check_ids']
        operation = serializer.validated_data['operation']
        
        try:
            if operation == 'delete':
                deleted_count = 0
                failed_count = 0
                
                for check_id in check_ids:
                    success = DocumentCheckService.delete_document_check(str(check_id))
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Deleted: {deleted_count}, Failed: {failed_count}.",
                    data={
                        'deleted_count': deleted_count,
                        'failed_count': failed_count,
                        'total_requested': len(check_ids),
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
