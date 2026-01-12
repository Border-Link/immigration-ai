"""
Admin API Views for VisaType Management

Admin-only endpoints for managing visa types.
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
    BaseAdminActivateAPI,
)
from rules_knowledge.services.visa_type_service import VisaTypeService
from rules_knowledge.serializers.visa_type.read import VisaTypeSerializer, VisaTypeListSerializer
from rules_knowledge.serializers.visa_type.admin import (
    VisaTypeAdminListQuerySerializer,
    VisaTypeActivateSerializer,
    BulkVisaTypeOperationSerializer,
)

logger = logging.getLogger('django')


class VisaTypeAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa types with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-types/
    Auth: Required (staff/superuser only)
    Query Params:
        - jurisdiction: Filter by jurisdiction
        - is_active: Filter by active status
        - code: Filter by code (partial match)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = VisaTypeAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        visa_types = VisaTypeService.get_by_filters(
            jurisdiction=validated_params.get('jurisdiction'),
            is_active=validated_params.get('is_active'),
            code=validated_params.get('code'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        from main_system.utils import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(visa_types, page=page, page_size=page_size)
        
        return self.api_response(
            message="Visa types retrieved successfully.",
            data={
                'items': VisaTypeListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaTypeAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed visa type information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-types/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa type"
    
    def get_entity_by_id(self, entity_id):
        """Get visa type by ID."""
        return VisaTypeService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return VisaTypeSerializer


class VisaTypeAdminActivateAPI(BaseAdminActivateAPI):
    """
    Admin: Activate or deactivate a visa type.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-types/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa type"
    
    def get_entity_by_id(self, entity_id):
        """Get visa type by ID."""
        return VisaTypeService.get_by_id(entity_id)
    
    def activate_entity(self, entity, is_active):
        """Activate or deactivate the visa type."""
        updated = VisaTypeService.activate_visa_type(entity, is_active)
        return updated is not None
    
    def post(self, request, id):
        """Override to return serialized data in response."""
        from main_system.serializers.admin.base import ActivateSerializer
        
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_active = serializer.validated_data['is_active']
        
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            updated = VisaTypeService.activate_visa_type(entity, is_active)
            if updated:
                action = "activated" if is_active else "deactivated"
                return self.api_response(
                    message=f"{self.get_entity_name()} {action} successfully.",
                    data=VisaTypeSerializer(updated).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to update {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error updating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaTypeAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete visa type.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-types/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa type"
    
    def get_entity_by_id(self, entity_id):
        """Get visa type by ID."""
        return VisaTypeService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the visa type."""
        return VisaTypeService.delete_visa_type(str(entity.id))


class BulkVisaTypeOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on visa types.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-types/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk visa type operation serializer."""
        return BulkVisaTypeOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa type"
    
    def get_entity_by_id(self, entity_id):
        """Get visa type by ID."""
        return VisaTypeService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the visa type."""
        if operation == 'activate':
            return VisaTypeService.activate_visa_type(entity, True)
        elif operation == 'deactivate':
            return VisaTypeService.activate_visa_type(entity, False)
        elif operation == 'delete':
            return VisaTypeService.delete_visa_type(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
