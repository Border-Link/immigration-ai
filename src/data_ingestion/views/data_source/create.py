from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_superadmin import IsSuperAdmin
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.serializers.data_source.create import DataSourceCreateSerializer
from data_ingestion.serializers.data_source.read import DataSourceSerializer


class DataSourceCreateAPI(AuthAPI):
    """Create a new data source."""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = DataSourceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data_source = DataSourceService.create_data_source(
            name=serializer.validated_data.get('name'),
            base_url=serializer.validated_data.get('base_url'),
            jurisdiction=serializer.validated_data.get('jurisdiction'),
            crawl_frequency=serializer.validated_data.get('crawl_frequency', 'daily'),
            is_active=serializer.validated_data.get('is_active', True)
        )

        if not data_source:
            return self.api_response(
                message="Error creating data source.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="Data source created successfully.",
            data=DataSourceSerializer(data_source).data,
            status_code=status.HTTP_201_CREATED
        )

