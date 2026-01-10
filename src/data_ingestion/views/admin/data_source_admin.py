"""
Admin API Views for DataSource Management

Admin-only endpoints for managing data sources.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.serializers.data_source.read import DataSourceSerializer, DataSourceListSerializer
from data_ingestion.serializers.data_source.admin import (
    DataSourceActivateSerializer,
    BulkDataSourceOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        jurisdiction = request.query_params.get('jurisdiction', None)
        is_active = request.query_params.get('is_active', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            is_active_bool = is_active.lower() == 'true' if is_active is not None else None
            
            # Use service method with filters
            sources = DataSourceService.get_by_filters(
                jurisdiction=jurisdiction,
                is_active=is_active_bool,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Data sources retrieved successfully.",
                data=DataSourceListSerializer(sources, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving data sources: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving data sources.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataSourceAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed data source information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/data-sources/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            source = DataSourceService.get_by_id(id)
            if not source:
                return self.api_response(
                    message=f"Data source with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Data source retrieved successfully.",
                data=DataSourceSerializer(source).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving data source {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving data source.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataSourceAdminActivateAPI(AuthAPI):
    """
    Admin: Activate or deactivate a data source.
    
    Endpoint: POST /api/v1/data-ingestion/admin/data-sources/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = DataSourceActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            source = DataSourceService.get_by_id(id)
            if not source:
                return self.api_response(
                    message=f"Data source with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_source = DataSourceService.activate_data_source(
                source,
                serializer.validated_data['is_active']
            )
            
            action = "activated" if serializer.validated_data['is_active'] else "deactivated"
            return self.api_response(
                message=f"Data source {action} successfully.",
                data=DataSourceSerializer(updated_source).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error activating/deactivating data source {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error activating/deactivating data source.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataSourceAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete data source.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/data-sources/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            source = DataSourceService.get_by_id(id)
            if not source:
                return self.api_response(
                    message=f"Data source with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = DataSourceService.delete_data_source(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting data source.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Data source deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting data source {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting data source.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDataSourceOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on data sources.
    
    Endpoint: POST /api/v1/data-ingestion/admin/data-sources/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkDataSourceOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data_source_ids = serializer.validated_data['data_source_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for data_source_id in data_source_ids:
                try:
                    source = DataSourceService.get_by_id(str(data_source_id))
                    if not source:
                        results['failed'].append({
                            'data_source_id': str(data_source_id),
                            'error': 'Data source not found'
                        })
                        continue
                    
                    if operation == 'activate':
                        DataSourceService.activate_data_source(source, True)
                        results['success'].append(str(data_source_id))
                    elif operation == 'deactivate':
                        DataSourceService.activate_data_source(source, False)
                        results['success'].append(str(data_source_id))
                    elif operation == 'delete':
                        deleted = DataSourceService.delete_data_source(str(data_source_id))
                        if deleted:
                            results['success'].append(str(data_source_id))
                        else:
                            results['failed'].append({
                                'data_source_id': str(data_source_id),
                                'error': 'Failed to delete'
                            })
                    elif operation == 'trigger_ingestion':
                        result = DataSourceService.trigger_ingestion(str(data_source_id), async_task=True)
                        if result.get('task_id') or result.get('success'):
                            results['success'].append(str(data_source_id))
                        else:
                            results['failed'].append({
                                'data_source_id': str(data_source_id),
                                'error': 'Failed to trigger ingestion'
                            })
                except Exception as e:
                    results['failed'].append({
                        'data_source_id': str(data_source_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
