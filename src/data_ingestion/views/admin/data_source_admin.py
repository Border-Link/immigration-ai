"""
Admin API Views for DataSource Management

Admin-only endpoints for managing data sources.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminActivateAPI,
)
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.serializers.data_source.read import DataSourceSerializer, DataSourceListSerializer
from data_ingestion.serializers.data_source.admin import (
    DataSourceAdminListQuerySerializer,
    DataSourceActivateSerializer,
    BulkDataSourceOperationSerializer,
)


class DataSourceAdminListAPI(AuthAPI):
    """
    Admin: Get list of all data sources with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/data-sources/
    Auth: Required (staff/superuser only)
    Query Params:
        - jurisdiction: Filter by jurisdiction
        - is_active: Filter by active status
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = DataSourceAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        sources = DataSourceService.get_by_filters(
            jurisdiction=query_serializer.validated_data.get('jurisdiction'),
            is_active=query_serializer.validated_data.get('is_active'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Data sources retrieved successfully.",
            data=DataSourceListSerializer(sources, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DataSourceAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed data source information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/data-sources/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Data source"
    
    def get_entity_by_id(self, entity_id):
        """Get data source by ID."""
        return DataSourceService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DataSourceSerializer


class DataSourceAdminActivateAPI(BaseAdminActivateAPI):
    """
    Admin: Activate or deactivate a data source.
    
    Endpoint: POST /api/v1/data-ingestion/admin/data-sources/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Data source"
    
    def get_entity_by_id(self, entity_id):
        """Get data source by ID."""
        return DataSourceService.get_by_id(entity_id)
    
    def activate_entity(self, entity, is_active):
        """Activate or deactivate the data source."""
        return DataSourceService.activate_data_source(entity, is_active)


class DataSourceAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete data source.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/data-sources/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Data source"
    
    def get_entity_by_id(self, entity_id):
        """Get data source by ID."""
        return DataSourceService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the data source."""
        return DataSourceService.delete_data_source(str(entity.id))


class BulkDataSourceOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on data sources.
    
    Endpoint: POST /api/v1/data-ingestion/admin/data-sources/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk data source operation serializer."""
        return BulkDataSourceOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Data source"
    
    def get_entity_by_id(self, entity_id):
        """Get data source by ID."""
        return DataSourceService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the data source."""
        if operation == 'activate':
            return DataSourceService.activate_data_source(entity, True)
        elif operation == 'deactivate':
            return DataSourceService.activate_data_source(entity, False)
        elif operation == 'delete':
            return DataSourceService.delete_data_source(str(entity.id))
        elif operation == 'trigger_ingestion':
            result = DataSourceService.trigger_ingestion(str(entity.id), async_task=True)
            return result if (result.get('task_id') or result.get('success')) else None
        else:
            raise ValueError(f"Invalid operation: {operation}")
