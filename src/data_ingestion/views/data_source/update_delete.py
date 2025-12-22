from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_superuser import IsSuperUser
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.serializers.data_source.update_delete import (
    DataSourceUpdateSerializer,
    DataSourceIngestionTriggerSerializer
)
from data_ingestion.serializers.data_source.read import DataSourceSerializer


class DataSourceUpdateAPI(AuthAPI):
    """Update a data source by ID."""
    permission_classes = [IsSuperUser]

    def patch(self, request, id):
        serializer = DataSourceUpdateSerializer(
            data=request.data,
            context={'data_source_id': id}
        )
        serializer.is_valid(raise_exception=True)

        data_source = DataSourceService.get_by_id(id)
        if not data_source:
            return self.api_response(
                message=f"Data source with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        updated_data_source = DataSourceService.update_data_source(
            data_source,
            **serializer.validated_data
        )

        if not updated_data_source:
            return self.api_response(
                message="Error updating data source.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="Data source updated successfully.",
            data=DataSourceSerializer(updated_data_source).data,
            status_code=status.HTTP_200_OK
        )


class DataSourceIngestionTriggerAPI(AuthAPI):
    """Trigger ingestion for a data source."""
    permission_classes = [IsSuperUser]

    def post(self, request, id):
        serializer = DataSourceIngestionTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data_source = DataSourceService.get_by_id(id)
        if not data_source:
            return self.api_response(
                message=f"Data source with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        async_task = serializer.validated_data.get('async_task', True)
        result = DataSourceService.trigger_ingestion(str(id), async_task=async_task)

        if not result.get('success') and not result.get('task_id'):
            return self.api_response(
                message="Error triggering ingestion.",
                data=result,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        message = "Ingestion task queued successfully." if async_task else "Ingestion completed successfully."
        return self.api_response(
            message=message,
            data=result,
            status_code=status.HTTP_200_OK
        )

