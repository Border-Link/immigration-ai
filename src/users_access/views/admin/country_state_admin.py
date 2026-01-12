"""
Admin API Views for Country and State/Province Management

Admin-only endpoints for managing countries and states/provinces.
Includes activation/deactivation endpoints.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.country_service import CountryService
from users_access.services.state_province_service import StateProvinceService
from users_access.serializers.country.read import CountrySerializer
from users_access.serializers.country.admin import (
    CountryActivateSerializer,
    CountrySetJurisdictionSerializer,
)
from users_access.serializers.state_province.read import StateProvinceSerializer
from users_access.serializers.state_province.admin import StateProvinceActivateSerializer


class CountryActivateAPI(AuthAPI):
    """
    Admin: Activate or deactivate a country.
    
    Endpoint: POST /api/v1/auth/admin/countries/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def post(self, request, id):
        serializer = CountryActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_country = CountryService.activate_country_by_id(
            id,
            serializer.validated_data['is_active']
        )
        if not updated_country:
            return self.api_response(
                message=f"Country with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        action = "activated" if serializer.validated_data['is_active'] else "deactivated"
        return self.api_response(
            message=f"Country {action} successfully.",
            data=CountrySerializer(updated_country).data,
            status_code=status.HTTP_200_OK
        )


class CountrySetJurisdictionAPI(AuthAPI):
    """
    Admin: Set country as jurisdiction or not.
    
    Endpoint: POST /api/v1/auth/admin/countries/<id>/set-jurisdiction/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def post(self, request, id):
        serializer = CountrySetJurisdictionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_country = CountryService.set_jurisdiction_by_id(
            id,
            serializer.validated_data['is_jurisdiction']
        )
        if not updated_country:
            return self.api_response(
                message=f"Country with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        action = "set as jurisdiction" if serializer.validated_data['is_jurisdiction'] else "removed as jurisdiction"
        return self.api_response(
            message=f"Country {action} successfully.",
            data=CountrySerializer(updated_country).data,
            status_code=status.HTTP_200_OK
        )


class StateProvinceActivateAPI(AuthAPI):
    """
    Admin: Activate or deactivate a state/province.
    
    Endpoint: POST /api/v1/auth/admin/states/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def post(self, request, id):
        serializer = StateProvinceActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_state = StateProvinceService.activate_state_province_by_id(
            id,
            serializer.validated_data['is_active']
        )
        if not updated_state:
            return self.api_response(
                message=f"State/Province with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        action = "activated" if serializer.validated_data['is_active'] else "deactivated"
        return self.api_response(
            message=f"State/Province {action} successfully.",
            data=StateProvinceSerializer(updated_state).data,
            status_code=status.HTTP_200_OK
        )
