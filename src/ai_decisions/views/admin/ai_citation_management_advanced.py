"""
Advanced Admin API Views for AICitation Management

Advanced admin-only endpoints for comprehensive AI citation management.
Includes updates, bulk operations, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.serializers.ai_citation.read import AICitationSerializer
from ai_decisions.serializers.ai_citation.admin import (
    AICitationAdminUpdateSerializer,
    BulkAICitationOperationSerializer,
)

logger = logging.getLogger('django')


class AICitationAdminUpdateAPI(AuthAPI):
    """
    Admin: Update AI citation.
    
    Endpoint: PATCH /api/v1/ai-decisions/admin/ai-citations/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = AICitationAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_citation = AICitationService.update_citation(
            id,
            **serializer.validated_data
        )
        
        if not updated_citation:
            return self.api_response(
                message=f"AI citation with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="AI citation updated successfully.",
            data=AICitationSerializer(updated_citation).data,
            status_code=status.HTTP_200_OK
        )


class BulkAICitationOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on AI citations.
    
    Endpoint: POST /api/v1/ai-decisions/admin/ai-citations/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkAICitationOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        citation_ids = serializer.validated_data['citation_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        for citation_id in citation_ids:
            if operation == 'delete':
                deleted = AICitationService.delete_citation(str(citation_id))
                if deleted:
                    results['success'].append(str(citation_id))
                else:
                    results['failed'].append({
                        'citation_id': str(citation_id),
                        'error': 'Failed to delete or citation not found'
                    })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
