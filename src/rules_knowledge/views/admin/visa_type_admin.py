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
    VisaTypeActivateSerializer,
    BulkVisaTypeOperationSerializer,
)
from django.utils.dateparse import parse_datetime

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
        jurisdiction = request.query_params.get('jurisdiction', None)
        is_active = request.query_params.get('is_active', None)
        code = request.query_params.get('code', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            is_active_bool = is_active.lower() == 'true' if is_active is not None else None
            
            # Use service method with filters
            visa_types = VisaTypeService.get_by_filters(
                jurisdiction=jurisdiction,
                is_active=is_active_bool,
                code=code,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Visa types retrieved successfully.",
                data=VisaTypeListSerializer(visa_types, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving visa types: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa types.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaTypeAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa type information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-types/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving visa type {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
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
        except Exception as e:
            logger.error(f"Error activating/deactivating visa type {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error activating/deactivating visa type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaTypeAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa type.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-types/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            visa_type = VisaTypeService.get_by_id(id)
            if not visa_type:
                return self.api_response(
                    message=f"Visa type with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = VisaTypeService.delete_visa_type(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting visa type.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Visa type deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting visa type {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting visa type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            for visa_type_id in visa_type_ids:
                try:
                    visa_type = VisaTypeService.get_by_id(str(visa_type_id))
                    if not visa_type:
                        results['failed'].append({
                            'visa_type_id': str(visa_type_id),
                            'error': 'Visa type not found'
                        })
                        continue
                    
                    if operation == 'activate':
                        VisaTypeService.activate_visa_type(visa_type, True)
                        results['success'].append(str(visa_type_id))
                    elif operation == 'deactivate':
                        VisaTypeService.activate_visa_type(visa_type, False)
                        results['success'].append(str(visa_type_id))
                    elif operation == 'delete':
                        deleted = VisaTypeService.delete_visa_type(str(visa_type_id))
                        if deleted:
                            results['success'].append(str(visa_type_id))
                        else:
                            results['failed'].append({
                                'visa_type_id': str(visa_type_id),
                                'error': 'Failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'visa_type_id': str(visa_type_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
