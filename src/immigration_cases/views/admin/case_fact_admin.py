"""
Admin API Views for CaseFact Management

Admin-only endpoints for managing case facts.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.serializers.case_fact.read import CaseFactSerializer, CaseFactListSerializer
from immigration_cases.serializers.case_fact.admin import (
    CaseFactAdminListQuerySerializer,
    CaseFactAdminUpdateSerializer,
    BulkCaseFactOperationSerializer,
)
from main_system.utils import paginate_queryset

logger = logging.getLogger('django')


class CaseFactAdminListAPI(AuthAPI):
    """
    Admin: Get list of all case facts with advanced filtering.
    
    Endpoint: GET /api/v1/immigration-cases/admin/case-facts/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - fact_key: Filter by fact key
        - source: Filter by source (user, ai, reviewer)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CaseFactAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        facts = CaseFactService.get_by_filters(
            case_id=str(validated_params.get('case_id')) if validated_params.get('case_id') else None,
            fact_key=validated_params.get('fact_key'),
            source=validated_params.get('source'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
        )
        
        return self.api_response(
            message="Case facts retrieved successfully.",
            data=CaseFactListSerializer(facts, many=True).data,
            status_code=status.HTTP_200_OK
        )


class CaseFactAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed case fact information.
    
    Endpoint: GET /api/v1/immigration-cases/admin/case-facts/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case fact"
    
    def get_entity_by_id(self, entity_id):
        """Get case fact by ID."""
        return CaseFactService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return CaseFactSerializer


class CaseFactAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update case fact value or source.
    
    Endpoint: PATCH /api/v1/immigration-cases/admin/case-facts/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case fact"
    
    def get_entity_by_id(self, entity_id):
        """Get case fact by ID."""
        return CaseFactService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return CaseFactAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return CaseFactSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the case fact."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return CaseFactService.update_case_fact(str(entity.id), **update_fields)


class CaseFactAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a case fact.
    
    Endpoint: DELETE /api/v1/immigration-cases/admin/case-facts/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case fact"
    
    def get_entity_by_id(self, entity_id):
        """Get case fact by ID."""
        return CaseFactService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the case fact."""
        return CaseFactService.delete_case_fact(str(entity.id))


class BulkCaseFactOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on case facts (delete, update_source).
    
    Endpoint: POST /api/v1/immigration-cases/admin/case-facts/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk case fact operation serializer."""
        return BulkCaseFactOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case fact"
    
    def get_entity_by_id(self, entity_id):
        """Get case fact by ID."""
        return CaseFactService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the case fact."""
        source = validated_data.get('source')
        
        if operation == 'delete':
            return CaseFactService.delete_case_fact(str(entity.id))
        elif operation == 'update_source':
            if not source:
                raise ValueError("source is required for 'update_source' operation.")
            return CaseFactService.update_case_fact(str(entity.id), source=source)
        else:
            raise ValueError(f"Invalid operation: {operation}")
    
    def get_success_data(self, entity, operation_result):
        """Get success data - return serialized fact for update operations, ID for delete."""
        if operation_result and hasattr(operation_result, 'id'):
            # For update operations, return serialized fact
            return CaseFactSerializer(operation_result).data
        # For delete operations, return ID
        return str(entity.id)
