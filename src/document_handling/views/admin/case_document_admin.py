"""
Admin API Views for CaseDocument Management

Admin-only endpoints for managing case documents.
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
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_reprocessing_service import DocumentReprocessingService
from document_handling.serializers.case_document.admin import (
    CaseDocumentAdminListQuerySerializer,
    CaseDocumentAdminListSerializer,
    CaseDocumentAdminDetailSerializer,
    CaseDocumentAdminUpdateSerializer,
    BulkCaseDocumentOperationSerializer,
)


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
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = CaseDocumentAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        documents = CaseDocumentService.get_by_filters(
            case_id=str(query_serializer.validated_data.get('case_id')) if query_serializer.validated_data.get('case_id') else None,
            document_type_id=str(query_serializer.validated_data.get('document_type_id')) if query_serializer.validated_data.get('document_type_id') else None,
            status=query_serializer.validated_data.get('status'),
            has_ocr_text=query_serializer.validated_data.get('has_ocr_text'),
            min_confidence=query_serializer.validated_data.get('min_confidence'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to'),
            mime_type=query_serializer.validated_data.get('mime_type'),
            has_expiry_date=query_serializer.validated_data.get('has_expiry_date'),
            expiry_date_from=query_serializer.validated_data.get('expiry_date_from'),
            expiry_date_to=query_serializer.validated_data.get('expiry_date_to'),
            content_validation_status=query_serializer.validated_data.get('content_validation_status'),
            is_expired=query_serializer.validated_data.get('is_expired')
        )
        
        return self.api_response(
            message="Case documents retrieved successfully.",
            data=CaseDocumentAdminListSerializer(documents, many=True).data,
            status_code=status.HTTP_200_OK
        )


class CaseDocumentAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed case document information.
    
    Endpoint: GET /api/v1/document-handling/admin/case-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case document"
    
    def get_entity_by_id(self, entity_id):
        """Get case document by ID."""
        return CaseDocumentService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return CaseDocumentAdminDetailSerializer


class CaseDocumentAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update case document.
    
    Endpoint: PUT /api/v1/document-handling/admin/case-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case document"
    
    def get_entity_by_id(self, entity_id):
        """Get case document by ID."""
        return CaseDocumentService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return CaseDocumentAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return CaseDocumentAdminDetailSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the case document."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return CaseDocumentService.update_case_document(str(entity.id), **update_fields)
    
    def put(self, request, id):
        """Override to support PUT method (base class uses PATCH)."""
        return self.patch(request, id)


class CaseDocumentAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a case document.
    
    Endpoint: DELETE /api/v1/document-handling/admin/case-documents/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case document"
    
    def get_entity_by_id(self, entity_id):
        """Get case document by ID."""
        return CaseDocumentService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the case document."""
        return CaseDocumentService.delete_case_document(str(entity.id))


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
    permission_classes = [AdminPermission]
    
    def post(self, request):
        serializer = BulkCaseDocumentOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document_ids = serializer.validated_data['document_ids']
        operation = serializer.validated_data['operation']
        
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
