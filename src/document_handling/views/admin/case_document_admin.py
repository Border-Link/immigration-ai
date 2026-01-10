"""
Admin API Views for CaseDocument Management

Admin-only endpoints for managing case documents.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_reprocessing_service import DocumentReprocessingService
from document_handling.serializers.case_document.admin import (
    CaseDocumentAdminListSerializer,
    CaseDocumentAdminDetailSerializer,
    CaseDocumentAdminUpdateSerializer,
    BulkCaseDocumentOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class CaseDocumentAdminListAPI(AuthAPI):
    """
    Admin: Get list of all case documents with advanced filtering.
    
    Endpoint: GET /api/v1/document-handling/admin/case-documents/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - document_type_id: Filter by document type ID
        - status: Filter by status (uploaded, processing, verified, rejected)
        - has_ocr_text: Filter by OCR text presence (true/false)
        - min_confidence: Filter by minimum classification confidence
        - mime_type: Filter by MIME type
        - date_from: Filter by uploaded date (from)
        - date_to: Filter by uploaded date (to)
        - has_expiry_date: Filter by expiry date presence (true/false)
        - expiry_date_from: Filter by expiry date (from) - ISO date format
        - expiry_date_to: Filter by expiry date (to) - ISO date format
        - content_validation_status: Filter by content validation status (pending, passed, failed, warning)
        - is_expired: Filter by expired documents (true/false)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        document_type_id = request.query_params.get('document_type_id', None)
        status_filter = request.query_params.get('status', None)
        has_ocr_text = request.query_params.get('has_ocr_text', None)
        min_confidence = request.query_params.get('min_confidence', None)
        mime_type = request.query_params.get('mime_type', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        has_expiry_date = request.query_params.get('has_expiry_date', None)
        expiry_date_from = request.query_params.get('expiry_date_from', None)
        expiry_date_to = request.query_params.get('expiry_date_to', None)
        content_validation_status = request.query_params.get('content_validation_status', None)
        is_expired = request.query_params.get('is_expired', None)
        
        try:
            # Parse parameters
            from django.utils.dateparse import parse_date
            parsed_date_from = parse_datetime(date_from) if date_from else None
            parsed_date_to = parse_datetime(date_to) if date_to else None
            parsed_expiry_date_from = parse_date(expiry_date_from) if expiry_date_from else None
            parsed_expiry_date_to = parse_date(expiry_date_to) if expiry_date_to else None
            has_ocr_text_bool = has_ocr_text.lower() == 'true' if has_ocr_text is not None else None
            has_expiry_date_bool = has_expiry_date.lower() == 'true' if has_expiry_date is not None else None
            is_expired_bool = is_expired.lower() == 'true' if is_expired is not None else None
            min_confidence_float = float(min_confidence) if min_confidence else None
            
            # Use service method with filters
            documents = CaseDocumentService.get_by_filters(
                case_id=case_id,
                document_type_id=document_type_id,
                status=status_filter,
                has_ocr_text=has_ocr_text_bool,
                min_confidence=min_confidence_float,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                mime_type=mime_type,
                has_expiry_date=has_expiry_date_bool,
                expiry_date_from=parsed_expiry_date_from,
                expiry_date_to=parsed_expiry_date_to,
                content_validation_status=content_validation_status,
                is_expired=is_expired_bool
            )
            
            return self.api_response(
                message="Case documents retrieved successfully.",
                data=CaseDocumentAdminListSerializer(documents, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving case documents: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case documents.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseDocumentAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed case document information.
    
    Endpoint: GET /api/v1/document-handling/admin/case-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            document = CaseDocumentService.get_by_id(id)
            if not document:
                return self.api_response(
                    message=f"Case document with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Case document retrieved successfully.",
                data=CaseDocumentAdminDetailSerializer(document).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving case document {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case document.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseDocumentAdminUpdateAPI(AuthAPI):
    """
    Admin: Update case document.
    
    Endpoint: PUT /api/v1/document-handling/admin/case-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def put(self, request, id):
        serializer = CaseDocumentAdminUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            update_fields = {}
            if 'document_type_id' in serializer.validated_data:
                update_fields['document_type_id'] = serializer.validated_data['document_type_id']
            if 'status' in serializer.validated_data:
                update_fields['status'] = serializer.validated_data['status']
            if 'classification_confidence' in serializer.validated_data:
                update_fields['classification_confidence'] = serializer.validated_data['classification_confidence']
            if 'ocr_text' in serializer.validated_data:
                update_fields['ocr_text'] = serializer.validated_data['ocr_text']
            if 'expiry_date' in serializer.validated_data:
                update_fields['expiry_date'] = serializer.validated_data['expiry_date']
            if 'content_validation_status' in serializer.validated_data:
                update_fields['content_validation_status'] = serializer.validated_data['content_validation_status']
            if 'content_validation_details' in serializer.validated_data:
                update_fields['content_validation_details'] = serializer.validated_data['content_validation_details']
            if 'extracted_metadata' in serializer.validated_data:
                update_fields['extracted_metadata'] = serializer.validated_data['extracted_metadata']
            
            updated_document = CaseDocumentService.update_case_document(id, **update_fields)
            if not updated_document:
                return self.api_response(
                    message=f"Case document with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Case document updated successfully.",
                data=CaseDocumentAdminDetailSerializer(updated_document).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating case document {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating case document.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseDocumentAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a case document.
    
    Endpoint: DELETE /api/v1/document-handling/admin/case-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            success = CaseDocumentService.delete_case_document(id)
            if not success:
                return self.api_response(
                    message=f"Case document with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Case document deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting case document {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting case document.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkCaseDocumentOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on case documents.
    
    Endpoint: POST /api/v1/document-handling/admin/case-documents/bulk-operation/
    Auth: Required (staff/superuser only)
    Body:
        {
            "document_ids": ["uuid1", "uuid2", ...],
            "operation": "delete" | "update_status" | "reprocess_ocr" | "reprocess_classification",
            "status": "verified" (required if operation is update_status)
        }
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkCaseDocumentOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        document_ids = serializer.validated_data['document_ids']
        operation = serializer.validated_data['operation']
        
        try:
            if operation == 'delete':
                deleted_count = 0
                failed_count = 0
                
                for doc_id in document_ids:
                    success = CaseDocumentService.delete_case_document(str(doc_id))
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Deleted: {deleted_count}, Failed: {failed_count}.",
                    data={
                        'deleted_count': deleted_count,
                        'failed_count': failed_count,
                        'total_requested': len(document_ids),
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
                
                for doc_id in document_ids:
                    updated = CaseDocumentService.update_status(str(doc_id), status_value)
                    if updated:
                        updated_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Updated: {updated_count}, Failed: {failed_count}.",
                    data={
                        'updated_count': updated_count,
                        'failed_count': failed_count,
                        'total_requested': len(document_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'reprocess_ocr':
                reprocessed_count = 0
                failed_count = 0
                
                for doc_id in document_ids:
                    success = DocumentReprocessingService.reprocess_ocr(str(doc_id))
                    if success:
                        reprocessed_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Reprocessed: {reprocessed_count}, Failed: {failed_count}.",
                    data={
                        'reprocessed_count': reprocessed_count,
                        'failed_count': failed_count,
                        'total_requested': len(document_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'reprocess_classification':
                reprocessed_count = 0
                failed_count = 0
                
                for doc_id in document_ids:
                    success = DocumentReprocessingService.reprocess_classification(str(doc_id))
                    if success:
                        reprocessed_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Reprocessed: {reprocessed_count}, Failed: {failed_count}.",
                    data={
                        'reprocessed_count': reprocessed_count,
                        'failed_count': failed_count,
                        'total_requested': len(document_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'reprocess_validation':
                reprocessed_count = 0
                failed_count = 0
                
                for doc_id in document_ids:
                    success = DocumentReprocessingService.reprocess_validation(str(doc_id))
                    if success:
                        reprocessed_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Reprocessed: {reprocessed_count}, Failed: {failed_count}.",
                    data={
                        'reprocessed_count': reprocessed_count,
                        'failed_count': failed_count,
                        'total_requested': len(document_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            elif operation == 'reprocess_full':
                reprocessed_count = 0
                failed_count = 0
                
                for doc_id in document_ids:
                    success = DocumentReprocessingService.reprocess_full(str(doc_id))
                    if success:
                        reprocessed_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Reprocessing initiated: {reprocessed_count}, Failed: {failed_count}.",
                    data={
                        'reprocessed_count': reprocessed_count,
                        'failed_count': failed_count,
                        'total_requested': len(document_ids),
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
