from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from main_system.permissions.admin_permission import AdminPermission
from users_access.services.country_service import CountryService
from users_access.serializers.country.read import (
    CountrySerializer,
    CountryListSerializer
)
from users_access.serializers.country.create import CountryCreateSerializer


class CountryListAPI(AuthAPI):
    """Get list of all active countries."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        countries = CountryService.get_all()
        return self.api_response(
            message="Countries retrieved successfully.",
            data=CountryListSerializer(countries, many=True).data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request):
        """
        Create a new country.
        Tests and legacy clients expect POST `/api/countries/` to create.
        """
        if not AdminPermission().has_permission(request, self):
            raise PermissionDenied("Admin permission required.")

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


class CountryDetailAPI(AuthAPI):
    """Get country by ID."""
    permission_classes = [AuthenticationPermission]

    def get(self, request, id):
        country = CountryService.get_by_id(id)
        if not country:
            return self.api_response(
                message=f"Country with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Country retrieved successfully.",
            data=CountrySerializer(country).data,
            status_code=status.HTTP_200_OK
        )


class CountryJurisdictionsAPI(AuthAPI):
    """Get all immigration jurisdictions."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        jurisdictions = CountryService.get_jurisdictions()
        return self.api_response(
            message="Jurisdictions retrieved successfully.",
            data=CountryListSerializer(jurisdictions, many=True).data,
            status_code=status.HTTP_200_OK
        )


class CountryWithStatesAPI(AuthAPI):
    """Get countries that have states/provinces."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        countries = CountryService.get_with_states()
        return self.api_response(
            message="Countries with states retrieved successfully.",
            data=CountryListSerializer(countries, many=True).data,
            status_code=status.HTTP_200_OK
        )


class CountrySearchAPI(AuthAPI):
    """Search countries by name."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        
        if not query:
            return self.api_response(
                message="Query parameter 'query' is required.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if len(query) < 2:
            return self.api_response(
                message="Search query must be at least 2 characters.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        countries = CountryService.search_by_name(query)
        return self.api_response(
            message="Search completed successfully.",
            data=CountryListSerializer(countries, many=True).data,
            status_code=status.HTTP_200_OK
        )

