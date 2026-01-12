"""
Admin API Views for VisaRequirement Management

Admin-only endpoints for managing visa requirements.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.serializers.visa_requirement.read import VisaRequirementSerializer, VisaRequirementListSerializer
from rules_knowledge.serializers.visa_requirement.admin import (
    VisaRequirementAdminListQuerySerializer,
    VisaRequirementUpdateSerializer,
    BulkVisaRequirementOperationSerializer,
)

logger = logging.getLogger('django')


class VisaRequirementAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa requirements with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-requirements/
    Auth: Required (staff/superuser only)
    Query Params:
        - rule_version_id: Filter by rule version
        - rule_type: Filter by rule type
        - is_mandatory: Filter by mandatory status
        - requirement_code: Filter by requirement code (partial match)
        - visa_type_id: Filter by visa type
        - jurisdiction: Filter by jurisdiction
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = VisaRequirementAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        requirements = VisaRequirementService.get_by_filters(
            rule_version_id=str(validated_params.get('rule_version_id')) if validated_params.get('rule_version_id') else None,
            rule_type=validated_params.get('rule_type'),
            is_mandatory=validated_params.get('is_mandatory'),
            requirement_code=validated_params.get('requirement_code'),
            visa_type_id=str(validated_params.get('visa_type_id')) if validated_params.get('visa_type_id') else None,
            jurisdiction=validated_params.get('jurisdiction'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        from main_system.utils import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(requirements, page=page, page_size=page_size)
        
        return self.api_response(
            message="Visa requirements retrieved successfully.",
            data={
                'items': VisaRequirementListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaRequirementAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed visa requirement information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-requirements/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa requirement by ID."""
        return VisaRequirementService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return VisaRequirementSerializer


class VisaRequirementAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update visa requirement.
    
    Endpoint: PATCH /api/v1/rules-knowledge/admin/visa-requirements/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa requirement by ID."""
        return VisaRequirementService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return VisaRequirementUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return VisaRequirementSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the visa requirement."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return VisaRequirementService.update_requirement(str(entity.id), **update_fields)


class VisaRequirementAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete visa requirement.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-requirements/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa requirement by ID."""
        return VisaRequirementService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the visa requirement."""
        return VisaRequirementService.delete_requirement(str(entity.id))


class BulkVisaRequirementOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on visa requirements.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-requirements/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk visa requirement operation serializer."""
        return BulkVisaRequirementOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa requirement by ID."""
        return VisaRequirementService.get_by_id(entity_id)
    
    def get_entity_ids(self, validated_data):
        """Override to use requirement_ids field name."""
        return validated_data.get('requirement_ids', [])
    
    def get_entity_id_field_name(self):
        """Override to use requirement_id field name."""
        return 'requirement_id'
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the visa requirement."""
        if operation == 'set_mandatory':
            return VisaRequirementService.update_requirement(str(entity.id), is_mandatory=True)
        elif operation == 'set_optional':
            return VisaRequirementService.update_requirement(str(entity.id), is_mandatory=False)
        elif operation == 'delete':
            return VisaRequirementService.delete_requirement(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
