from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.country_service import CountryService
from users_access.serializers.country.update_delete import (
    CountryUpdateSerializer,
    CountryDeleteSerializer
)
from users_access.serializers.country.read import CountrySerializer


class CountryUpdateAPI(AuthAPI):
    """Update a country by ID. Only admin/staff can access."""
    permission_classes = [AdminPermission]

    def patch(self, request, id):
        serializer = CountryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        country = CountryService.get_by_id(id)
        if not country:
            return self.api_response(
                message=f"Country with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        updated_country = CountryService.update_country(
            country,
            **serializer.validated_data
        )

        if not updated_country:
            return self.api_response(
                message="Error updating country.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="Country updated successfully.",
            data=CountrySerializer(updated_country).data,
            status_code=status.HTTP_200_OK
        )


class CountryDeleteAPI(AuthAPI):
    """Delete a country and all its states/provinces. Only admin/staff can access."""
    permission_classes = [AdminPermission]

    def delete(self, request, id):
        serializer = CountryDeleteSerializer(data={'id': id})
        serializer.is_valid(raise_exception=True)

        country_id = serializer.validated_data.get('id')
        deleted = CountryService.delete_country_by_id(country_id)
        if not deleted:
            return self.api_response(
                message="Error deleting country.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return self.api_response(
            message="Country and all its states/provinces deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

