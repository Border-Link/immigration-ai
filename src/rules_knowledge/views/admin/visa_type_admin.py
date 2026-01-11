"""
Admin API Views for VisaType Management

Admin-only endpoints for managing visa types.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
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
    permission_classes = [IsAdminOrStaff]
    
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
        from rules_knowledge.helpers.pagination import paginate_queryset
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


class VisaTypeAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa type information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-types/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        visa_type = VisaTypeService.get_by_id(id)
        if not visa_type:
            return self.api_response(
                message=f"Visa type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa type retrieved successfully.",
            data=VisaTypeSerializer(visa_type).data,
            status_code=status.HTTP_200_OK
        )


class VisaTypeAdminActivateAPI(AuthAPI):
    """
    Admin: Activate or deactivate a visa type.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-types/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = VisaTypeActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        visa_type = VisaTypeService.get_by_id(id)
        if not visa_type:
            return self.api_response(
                message=f"Visa type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        updated_visa_type = VisaTypeService.activate_visa_type(
            visa_type,
            serializer.validated_data['is_active']
        )
        
        action = "activated" if serializer.validated_data['is_active'] else "deactivated"
        return self.api_response(
            message=f"Visa type {action} successfully.",
            data=VisaTypeSerializer(updated_visa_type).data,
            status_code=status.HTTP_200_OK
        )


class VisaTypeAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa type.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-types/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = VisaTypeService.delete_visa_type(id)
        if not deleted:
            return self.api_response(
                message=f"Visa type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa type deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )


class BulkVisaTypeOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on visa types.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-types/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkVisaTypeOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        visa_type_ids = serializer.validated_data['visa_type_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        for visa_type_id in visa_type_ids:
            visa_type = VisaTypeService.get_by_id(str(visa_type_id))
            if not visa_type:
                results['failed'].append({
                    'visa_type_id': str(visa_type_id),
                    'error': 'Visa type not found'
                })
                continue
            
            if operation == 'activate':
                updated = VisaTypeService.activate_visa_type(visa_type, True)
                if updated:
                    results['success'].append(str(visa_type_id))
                else:
                    results['failed'].append({
                        'visa_type_id': str(visa_type_id),
                        'error': 'Failed to activate'
                    })
            elif operation == 'deactivate':
                updated = VisaTypeService.activate_visa_type(visa_type, False)
                if updated:
                    results['success'].append(str(visa_type_id))
                else:
                    results['failed'].append({
                        'visa_type_id': str(visa_type_id),
                        'error': 'Failed to deactivate'
                    })
            elif operation == 'delete':
                deleted = VisaTypeService.delete_visa_type(str(visa_type_id))
                if deleted:
                    results['success'].append(str(visa_type_id))
                else:
                    results['failed'].append({
                        'visa_type_id': str(visa_type_id),
                        'error': 'Failed to delete'
                    })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
