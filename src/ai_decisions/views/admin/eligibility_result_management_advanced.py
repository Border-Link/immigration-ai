"""
Advanced Admin API Views for EligibilityResult Management

Advanced admin-only endpoints for comprehensive eligibility result management.
Includes bulk operations, updates, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import BaseAdminUpdateAPI
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.serializers.eligibility_result.read import EligibilityResultSerializer
from ai_decisions.serializers.eligibility_result.admin import (
    EligibilityResultAdminUpdateSerializer,
    BulkEligibilityResultOperationSerializer,
)

logger = logging.getLogger('django')


class EligibilityResultAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update eligibility result.
    
    Endpoint: PATCH /api/v1/ai-decisions/admin/eligibility-results/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Eligibility result"
    
    def get_entity_by_id(self, entity_id):
        """Get eligibility result by ID."""
        return EligibilityResultService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return EligibilityResultAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return EligibilityResultSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the eligibility result."""
        return EligibilityResultService.update_eligibility_result(
            str(entity.id),
            **validated_data
        )


class BulkEligibilityResultOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on eligibility results.
    
    Endpoint: POST /api/v1/ai-decisions/admin/eligibility-results/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk eligibility result operation serializer."""
        return BulkEligibilityResultOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Eligibility result"
    
    def get_entity_by_id(self, entity_id):
        """Get eligibility result by ID."""
        return EligibilityResultService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the eligibility result."""
        if operation == 'delete':
            return EligibilityResultService.delete_eligibility_result(str(entity.id))
        elif operation == 'update_outcome':
            update_data = {}
            if 'outcome' in validated_data:
                update_data['outcome'] = validated_data['outcome']
            if 'confidence' in validated_data:
                update_data['confidence'] = validated_data['confidence']
            if 'reasoning_summary' in validated_data:
                update_data['reasoning_summary'] = validated_data['reasoning_summary']
            
            return EligibilityResultService.update_eligibility_result(
                str(entity.id),
                **update_data
            )
        else:
            raise ValueError(f"Invalid operation: {operation}")
