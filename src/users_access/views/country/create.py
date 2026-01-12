from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.country_service import CountryService
from users_access.serializers.country.create import CountryCreateSerializer
from users_access.serializers.country.read import CountrySerializer


class CountryCreateAPI(AuthAPI):
    """Create a new country. Only admin/staff can access."""
    permission_classes = [AdminPermission]

    def post(self, request):
        serializer = CountryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        country = CountryService.create_country(
            code=serializer.validated_data.get('code'),
            name=serializer.validated_data.get('name'),
            has_states=serializer.validated_data.get('has_states', False),
            is_jurisdiction=serializer.validated_data.get('is_jurisdiction', False)
        )

        if not country:
            return self.api_response(
                message="Country already exists or error creating country.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Country created successfully.",
            data=CountrySerializer(country).data,
            status_code=status.HTTP_201_CREATED
        )

