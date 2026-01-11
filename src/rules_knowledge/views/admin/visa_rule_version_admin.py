"""
Admin API Views for VisaRuleVersion Management

Admin-only endpoints for managing visa rule versions.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer, VisaRuleVersionListSerializer
from rules_knowledge.serializers.visa_rule_version.admin import (
    VisaRuleVersionAdminListQuerySerializer,
    VisaRuleVersionPublishSerializer,
    VisaRuleVersionUpdateSerializer,
    BulkVisaRuleVersionOperationSerializer,
)


class VisaRuleVersionAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa rule versions with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-rule-versions/
    Auth: Required (staff/superuser only)
    Query Params:
        - visa_type_id: Filter by visa type
        - is_published: Filter by published status
        - jurisdiction: Filter by jurisdiction
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - effective_from: Filter by effective_from date
        - effective_to: Filter by effective_to date
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = VisaRuleVersionAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        rule_versions = VisaRuleVersionService.get_by_filters(
            visa_type_id=str(validated_params.get('visa_type_id')) if validated_params.get('visa_type_id') else None,
            is_published=validated_params.get('is_published'),
            jurisdiction=validated_params.get('jurisdiction'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
            effective_from=validated_params.get('effective_from'),
            effective_to=validated_params.get('effective_to')
        )
        
        # Paginate results
        from main_system.utils import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(rule_versions, page=page, page_size=page_size)
        
        return self.api_response(
            message="Visa rule versions retrieved successfully.",
            data={
                'items': VisaRuleVersionListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed visa rule version information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa rule version"
    
    def get_entity_by_id(self, entity_id):
        """Get visa rule version by ID."""
        return VisaRuleVersionService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return VisaRuleVersionSerializer


class VisaRuleVersionAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update visa rule version.
    
    Endpoint: PATCH /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa rule version"
    
    def get_entity_by_id(self, entity_id):
        """Get visa rule version by ID."""
        return VisaRuleVersionService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return VisaRuleVersionUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return VisaRuleVersionSerializer
    
    def patch(self, request, id):
        """Override to handle optimistic locking and user context."""
        entity = self.get_entity_by_id(id)
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract version for optimistic locking if provided
        validated_data = serializer.validated_data.copy()
        expected_version = validated_data.pop('version', None)
        updated_by = request.user if request.user.is_authenticated else None
        
        updated_rule_version = VisaRuleVersionService.update_rule_version(
            str(entity.id),
            updated_by=updated_by,
            expected_version=expected_version,
            **validated_data
        )
        
        if not updated_rule_version:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        response_serializer = self.get_response_serializer_class()
        if response_serializer:
            response_data = response_serializer(updated_rule_version).data
        else:
            response_data = serializer_class(updated_rule_version).data
        
        return self.api_response(
            message=f"{self.get_entity_name()} updated successfully.",
            data=response_data,
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionAdminPublishAPI(AuthAPI):
    """
    Admin: Publish or unpublish a visa rule version.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/publish/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = VisaRuleVersionPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rule_version = VisaRuleVersionService.get_by_id(id)
        if not rule_version:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Extract version for optimistic locking if provided
        expected_version = serializer.validated_data.get('version')
        published_by = request.user if request.user.is_authenticated else None
        
        # Use publish_rule_version for proper optimistic locking support
        if serializer.validated_data['is_published']:
            updated_rule_version = VisaRuleVersionService.publish_rule_version(
                id, published_by=published_by, expected_version=expected_version
            )
        else:
            # For unpublish, use update_rule_version
            updated_rule_version = VisaRuleVersionService.update_rule_version(
                id, updated_by=published_by, expected_version=expected_version, is_published=False
            )
        
        if not updated_rule_version:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        action = "published" if serializer.validated_data['is_published'] else "unpublished"
        return self.api_response(
            message=f"Visa rule version {action} successfully.",
            data=VisaRuleVersionSerializer(updated_rule_version).data,
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete visa rule version.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa rule version"
    
    def get_entity_by_id(self, entity_id):
        """Get visa rule version by ID."""
        return VisaRuleVersionService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the visa rule version."""
        return VisaRuleVersionService.delete_rule_version(str(entity.id))


class BulkVisaRuleVersionOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on visa rule versions.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-rule-versions/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk visa rule version operation serializer."""
        return BulkVisaRuleVersionOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa rule version"
    
    def get_entity_by_id(self, entity_id):
        """Get visa rule version by ID."""
        return VisaRuleVersionService.get_by_id(entity_id)
    
    def get_entity_ids(self, validated_data):
        """Override to use rule_version_ids field name."""
        return validated_data.get('rule_version_ids', [])
    
    def get_entity_id_field_name(self):
        """Override to use rule_version_id field name."""
        return 'rule_version_id'
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the visa rule version."""
        if operation == 'publish':
            VisaRuleVersionService.publish_rule_version_by_flag(entity, True)
            return entity
        elif operation == 'unpublish':
            VisaRuleVersionService.publish_rule_version_by_flag(entity, False)
            return entity
        elif operation == 'delete':
            return VisaRuleVersionService.delete_rule_version(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
