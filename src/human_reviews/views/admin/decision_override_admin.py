"""
Admin API Views for DecisionOverride Management

Admin-only endpoints for managing decision overrides.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from human_reviews.services.decision_override_service import DecisionOverrideService
from human_reviews.serializers.decision_override.read import DecisionOverrideSerializer, DecisionOverrideListSerializer
from human_reviews.serializers.decision_override.admin import (
    DecisionOverrideAdminListQuerySerializer,
    DecisionOverrideAdminUpdateSerializer,
    BulkDecisionOverrideOperationSerializer,
)


class DecisionOverrideAdminListAPI(AuthAPI):
    """
    Admin: Get list of all decision overrides with advanced filtering.
    
    Endpoint: GET /api/v1/human-reviews/admin/decision-overrides/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - reviewer_id: Filter by reviewer ID
        - original_result_id: Filter by original eligibility result ID
        - overridden_outcome: Filter by overridden outcome (eligible, not_eligible, requires_review)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = DecisionOverrideAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        overrides = DecisionOverrideService.get_by_filters(
            case_id=str(query_serializer.validated_data.get('case_id')) if query_serializer.validated_data.get('case_id') else None,
            reviewer_id=str(query_serializer.validated_data.get('reviewer_id')) if query_serializer.validated_data.get('reviewer_id') else None,
            original_result_id=str(query_serializer.validated_data.get('original_result_id')) if query_serializer.validated_data.get('original_result_id') else None,
            overridden_outcome=query_serializer.validated_data.get('overridden_outcome'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Decision overrides retrieved successfully.",
            data=DecisionOverrideListSerializer(overrides, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DecisionOverrideAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed decision override information.
    
    Endpoint: GET /api/v1/human-reviews/admin/decision-overrides/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Decision override"
    
    def get_entity_by_id(self, entity_id):
        """Get decision override by ID."""
        return DecisionOverrideService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DecisionOverrideSerializer


class DecisionOverrideAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update decision override.
    
    Endpoint: PUT /api/v1/human-reviews/admin/decision-overrides/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Decision override"
    
    def get_entity_by_id(self, entity_id):
        """Get decision override by ID."""
        return DecisionOverrideService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return DecisionOverrideAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return DecisionOverrideSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the decision override."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return DecisionOverrideService.update_decision_override(str(entity.id), **update_fields)
    
    def put(self, request, id):
        """Override to support PUT method (base class uses PATCH)."""
        return self.patch(request, id)


class DecisionOverrideAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete decision override.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/decision-overrides/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Decision override"
    
    def get_entity_by_id(self, entity_id):
        """Get decision override by ID."""
        return DecisionOverrideService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the decision override."""
        return DecisionOverrideService.delete_decision_override(str(entity.id))


class BulkDecisionOverrideOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on decision overrides.
    
    Endpoint: POST /api/v1/human-reviews/admin/decision-overrides/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk decision override operation serializer."""
        return BulkDecisionOverrideOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Decision override"
    
    def get_entity_by_id(self, entity_id):
        """Get decision override by ID."""
        return DecisionOverrideService.get_by_id(entity_id)
    
    def get_entity_ids(self, validated_data):
        """Override to use decision_override_ids field name."""
        return validated_data.get('decision_override_ids', [])
    
    def get_entity_id_field_name(self):
        """Override to use override_id field name."""
        return 'override_id'
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the decision override."""
        if operation == 'delete':
            return DecisionOverrideService.delete_decision_override(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
