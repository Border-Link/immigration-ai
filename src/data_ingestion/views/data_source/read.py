from rest_framework import status
from main_system.base.auth_api import AuthAPI
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.serializers.data_source.read import (
    DataSourceSerializer,
    DataSourceListSerializer
)


class DataSourceListAPI(AuthAPI):
    """Get all data sources."""

    def get(self, request):
        jurisdiction = request.query_params.get('jurisdiction', None)
        
        if jurisdiction:
            data_sources = DataSourceService.get_by_jurisdiction(jurisdiction)
        else:
            data_sources = DataSourceService.get_all()

        return self.api_response(
            message="Data sources retrieved successfully.",
            data=DataSourceListSerializer(data_sources, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DataSourceDetailAPI(AuthAPI):
    """Get data source by ID."""

    def get(self, request, id):
        data_source = DataSourceService.get_by_id(id)
        
        if not data_source:
            return self.api_response(
                message=f"Data source with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Data source retrieved successfully.",
            data=DataSourceSerializer(data_source).data,
            status_code=status.HTTP_200_OK
        )

