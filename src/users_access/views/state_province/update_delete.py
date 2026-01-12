from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.state_province_service import StateProvinceService
from users_access.serializers.state_province.update_delete import (
    StateProvinceUpdateSerializer,
    StateProvinceDeleteSerializer
)
from users_access.serializers.state_province.read import StateProvinceSerializer


class StateProvinceUpdateAPI(AuthAPI):
    """Update a state/province by ID. Only admin/staff can access."""
    permission_classes = [AdminPermission]

    def patch(self, request, id):
        serializer = StateProvinceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        state = StateProvinceService.get_by_id(id)
        if not state:
            return self.api_response(
                message=f"State/Province with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        updated_state = StateProvinceService.update_state_province(
            state,
            **serializer.validated_data
        )

        if not updated_state:
            return self.api_response(
                message="Error updating state/province.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="State/province updated successfully.",
            data=StateProvinceSerializer(updated_state).data,
            status_code=status.HTTP_200_OK
        )


class StateProvinceDeleteAPI(AuthAPI):
    """Delete a state/province. Only admin/staff can access."""
    permission_classes = [AdminPermission]

    def delete(self, request, id):
        serializer = StateProvinceDeleteSerializer(data={'id': id})
        serializer.is_valid(raise_exception=True)

        state_id = serializer.validated_data.get('id')
        deleted = StateProvinceService.delete_state_province_by_id(state_id)
        if not deleted:
            return self.api_response(
                message="Error deleting state/province.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return self.api_response(
            message="State/province deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

