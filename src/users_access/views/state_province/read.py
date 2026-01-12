from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.state_province_service import StateProvinceService
from users_access.serializers.state_province.read import (
    StateProvinceSerializer,
    StateProvinceListSerializer
)


class StateProvinceListAPI(AuthAPI):
    """Get states/provinces by country ID."""
    permission_classes = [AuthenticationPermission]

    def get(self, request, country_id):
        states = StateProvinceService.get_by_country_id(country_id)
        return self.api_response(
            message="States/Provinces retrieved successfully.",
            data=StateProvinceListSerializer(states, many=True).data,
            status_code=status.HTTP_200_OK
        )


class StateProvinceDetailAPI(AuthAPI):
    """Get specific state/province by ID."""
    permission_classes = [AuthenticationPermission]

    def get(self, request, id):
        state = StateProvinceService.get_by_id(id)
        if not state:
            return self.api_response(
                message=f"State/Province with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="State/Province retrieved successfully.",
            data=StateProvinceSerializer(state).data,
            status_code=status.HTTP_200_OK
        )


class StateProvinceNominationProgramsAPI(AuthAPI):
    """Get states/provinces with nomination programs."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        country_id = request.query_params.get('country_id', None)

        states = StateProvinceService.get_nomination_programs(country_id=country_id)
        return self.api_response(
            message="Nomination programs retrieved successfully.",
            data=StateProvinceListSerializer(states, many=True).data,
            status_code=status.HTTP_200_OK
        )

