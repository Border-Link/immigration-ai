from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.state_province_service import StateProvinceService
from users_access.serializers.state_province.create import StateProvinceCreateSerializer
from users_access.serializers.state_province.read import StateProvinceSerializer


class StateProvinceCreateAPI(AuthAPI):
    """Create a new state/province. Only admin/staff can access."""
    permission_classes = [AdminPermission]

    def post(self, request):
        serializer = StateProvinceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        state = StateProvinceService.create_state_province(
            country_id=serializer.validated_data.get('country_id'),
            code=serializer.validated_data.get('code'),
            name=serializer.validated_data.get('name'),
            has_nomination_program=serializer.validated_data.get('has_nomination_program', False)
        )

        if not state:
            return self.api_response(
                message="State/province already exists or error creating state/province.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="State/province created successfully.",
            data=StateProvinceSerializer(state).data,
            status_code=status.HTTP_201_CREATED
        )

