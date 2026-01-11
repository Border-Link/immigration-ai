"""
Advanced Admin API Views for AIReasoningLog Management

Advanced admin-only endpoints for comprehensive AI reasoning log management.
Includes bulk operations, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from ai_decisions.services.ai_reasoning_log_service import AIReasoningLogService
from ai_decisions.serializers.ai_reasoning_log.admin import BulkAIReasoningLogOperationSerializer

logger = logging.getLogger('django')


class BulkAIReasoningLogOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on AI reasoning logs.
    
    Endpoint: POST /api/v1/ai-decisions/admin/ai-reasoning-logs/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk AI reasoning log operation serializer."""
        return BulkAIReasoningLogOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "AI reasoning log"
    
    def get_entity_by_id(self, entity_id):
        """Get AI reasoning log by ID."""
        return AIReasoningLogService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the AI reasoning log."""
        if operation == 'delete':
            return AIReasoningLogService.delete_reasoning_log(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
