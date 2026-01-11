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
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import BaseAdminUpdateAPI
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.serializers.ai_citation.read import AICitationSerializer
from ai_decisions.serializers.ai_citation.admin import (
    AICitationAdminUpdateSerializer,
    BulkAICitationOperationSerializer,
)

logger = logging.getLogger('django')


class AICitationAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update AI citation.
    
    Endpoint: PATCH /api/v1/ai-decisions/admin/ai-citations/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "AI citation"
    
    def get_entity_by_id(self, entity_id):
        """Get AI citation by ID."""
        return AICitationService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return AICitationAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return AICitationSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the AI citation."""
        return AICitationService.update_citation(
            str(entity.id),
            **validated_data
        )


class BulkAICitationOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on AI citations.
    
    Endpoint: POST /api/v1/ai-decisions/admin/ai-citations/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk AI citation operation serializer."""
        return BulkAICitationOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "AI citation"
    
    def get_entity_by_id(self, entity_id):
        """Get AI citation by ID."""
        return AICitationService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the AI citation."""
        if operation == 'delete':
            return AICitationService.delete_citation(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
