"""
Admin Serializers for DataSource Management

Serializers for admin data source management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import (
    BaseAdminListQuerySerializer,
    ActivateSerializer as BaseActivateSerializer
)
from data_ingestion.models.data_source import DataSource


class DataSourceAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    jurisdiction = serializers.CharField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, allow_null=True)

    def to_internal_value(self, data):
        """Parse string dates to datetime objects and boolean values."""
        # Parse boolean strings before calling super
        if 'is_active' in data and data.get('is_active') is not None:
            if isinstance(data['is_active'], str):
                data['is_active'] = data['is_active'].lower() == 'true'
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


class DataSourceActivateSerializer(BaseActivateSerializer):
    """Serializer for activating/deactivating a data source."""
    pass


class BulkDataSourceOperationSerializer(serializers.Serializer):
    """Serializer for bulk data source operations."""
    data_source_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'activate',
        'deactivate',
        'delete',
        'trigger_ingestion',
    ])
