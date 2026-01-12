"""
Admin API Views for ParsedRule Management

Admin-only endpoints for managing parsed rules.
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
from data_ingestion.services.parsed_rule_service import ParsedRuleService
from data_ingestion.serializers.parsed_rule.read import ParsedRuleSerializer, ParsedRuleListSerializer
from data_ingestion.serializers.parsed_rule.admin import (
    ParsedRuleAdminListQuerySerializer,
    ParsedRuleAdminUpdateSerializer,
    BulkParsedRuleOperationSerializer,
)


class ParsedRuleAdminListAPI(AuthAPI):
    """
    Admin: Get list of all parsed rules with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/parsed-rules/
    Auth: Required (staff/superuser only)
    Query Params:
        - status: Filter by status
        - visa_code: Filter by visa code
        - rule_type: Filter by rule type
        - min_confidence: Filter by minimum confidence
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = ParsedRuleAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        rules = ParsedRuleService.get_by_filters(
            status=query_serializer.validated_data.get('status'),
            visa_code=query_serializer.validated_data.get('visa_code'),
            rule_type=query_serializer.validated_data.get('rule_type'),
            min_confidence=query_serializer.validated_data.get('min_confidence'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Parsed rules retrieved successfully.",
            data=ParsedRuleListSerializer(rules, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ParsedRuleAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed parsed rule information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/parsed-rules/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Parsed rule"
    
    def get_entity_by_id(self, entity_id):
        """Get parsed rule by ID."""
        return ParsedRuleService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return ParsedRuleSerializer


class ParsedRuleAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update parsed rule.
    
    Endpoint: PATCH /api/v1/data-ingestion/admin/parsed-rules/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Parsed rule"
    
    def get_entity_by_id(self, entity_id):
        """Get parsed rule by ID."""
        return ParsedRuleService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return ParsedRuleAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return ParsedRuleSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the parsed rule."""
        return ParsedRuleService.update_parsed_rule(
            str(entity.id),
            **validated_data
        )


class ParsedRuleAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete parsed rule.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/parsed-rules/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Parsed rule"
    
    def get_entity_by_id(self, entity_id):
        """Get parsed rule by ID."""
        return ParsedRuleService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the parsed rule."""
        return ParsedRuleService.delete_parsed_rule(str(entity.id))


class BulkParsedRuleOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on parsed rules.
    
    Endpoint: POST /api/v1/data-ingestion/admin/parsed-rules/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk parsed rule operation serializer."""
        return BulkParsedRuleOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Parsed rule"
    
    def get_entity_by_id(self, entity_id):
        """Get parsed rule by ID."""
        return ParsedRuleService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the parsed rule."""
        if operation == 'delete':
            return ParsedRuleService.delete_parsed_rule(str(entity.id))
        elif operation == 'approve':
            return ParsedRuleService.update_status(str(entity.id), 'approved')
        elif operation == 'reject':
            return ParsedRuleService.update_status(str(entity.id), 'rejected')
        elif operation == 'mark_pending':
            return ParsedRuleService.update_status(str(entity.id), 'pending')
        else:
            raise ValueError(f"Invalid operation: {operation}")
