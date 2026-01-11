"""
Admin API Views for Case Management

Admin-only endpoints for managing cases.
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
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer, CaseListSerializer
from immigration_cases.serializers.case.admin import (
    CaseAdminListQuerySerializer,
    CaseAdminUpdateSerializer,
    BulkCaseOperationSerializer,
)
from main_system.utils import paginate_queryset

logger = logging.getLogger('django')


class CaseAdminListAPI(AuthAPI):
    """
    Admin: Get list of all cases with advanced filtering.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/
    Auth: Required (staff/superuser only)
    Query Params:
        - user_id: Filter by user ID
        - jurisdiction: Filter by jurisdiction
        - status: Filter by case status
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - updated_date_from: Filter by updated date (from)
        - updated_date_to: Filter by updated date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CaseAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        cases = CaseService.get_by_filters(
            user_id=str(validated_params.get('user_id')) if validated_params.get('user_id') else None,
            jurisdiction=validated_params.get('jurisdiction'),
            status=validated_params.get('status'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
            updated_date_from=validated_params.get('updated_date_from'),
            updated_date_to=validated_params.get('updated_date_to'),
        )
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_cases, pagination_metadata = paginate_queryset(cases, page=page, page_size=page_size)
        
        return self.api_response(
            message="Cases retrieved successfully.",
            data={
                'items': CaseListSerializer(paginated_cases, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class CaseAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed case information.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case"
    
    def get_entity_by_id(self, entity_id):
        """Get case by ID."""
        return CaseService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return CaseSerializer


class CaseAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update case status or jurisdiction.
    
    Endpoint: PATCH /api/v1/immigration-cases/admin/cases/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case"
    
    def get_entity_by_id(self, entity_id):
        """Get case by ID."""
        return CaseService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return CaseAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return CaseSerializer
    
    def patch(self, request, id):
        """Override to handle optimistic locking, user context, and custom error handling."""
        entity = self.get_entity_by_id(id)
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Extract version and reason for optimistic locking and history tracking
        validated_data = serializer.validated_data.copy()
        version = validated_data.pop('version', None)
        reason = validated_data.pop('reason', None)
        
        updated_case, error_message, http_status = CaseService.update_case(
            str(entity.id),
            updated_by_id=str(request.user.id) if request.user and request.user.is_authenticated else None,
            reason=reason,
            version=version,
            **validated_data
        )
        
        if not updated_case:
            status_code = status.HTTP_404_NOT_FOUND if http_status == 404 else (
                status.HTTP_409_CONFLICT if http_status == 409 else (
                    status.HTTP_400_BAD_REQUEST if http_status == 400 else status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            )
            return self.api_response(
                message=error_message or f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status_code
            )
        
        response_serializer = self.get_response_serializer_class()
        if response_serializer:
            response_data = response_serializer(updated_case).data
        else:
            response_data = serializer_class(updated_case).data
        
        return self.api_response(
            message=f"{self.get_entity_name()} updated successfully.",
            data=response_data,
            status_code=status.HTTP_200_OK
        )


class CaseAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a case.
    
    Endpoint: DELETE /api/v1/immigration-cases/admin/cases/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case"
    
    def get_entity_by_id(self, entity_id):
        """Get case by ID."""
        return CaseService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the case."""
        return CaseService.delete_case(str(entity.id))


class BulkCaseOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on cases (update_status, delete, archive).
    
    Endpoint: POST /api/v1/immigration-cases/admin/cases/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk case operation serializer."""
        return BulkCaseOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Case"
    
    def get_entity_by_id(self, entity_id):
        """Get case by ID."""
        return CaseService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the case."""
        status_value = validated_data.get('status')
        jurisdiction = validated_data.get('jurisdiction')
        
        if operation == 'update_status':
            if not status_value:
                raise ValueError("status is required for 'update_status' operation.")
            return CaseService.update_case(str(entity.id), status=status_value)
        elif operation == 'delete':
            return CaseService.delete_case(str(entity.id))
        elif operation == 'archive':
            # Archive is essentially updating status to 'closed'
            return CaseService.update_case(str(entity.id), status='closed')
        else:
            raise ValueError(f"Invalid operation: {operation}")
    
    def get_success_data(self, entity, operation_result):
        """Get success data - return serialized case for update operations, ID for delete."""
        if operation_result and hasattr(operation_result, 'id'):
            # For update operations, return serialized case
            return CaseSerializer(operation_result).data
        # For delete operations, return ID
        return str(entity.id)
