"""
Admin Serializers for DataSource Management

Serializers for admin data source management operations.
"""
from rest_framework import serializers
from data_ingestion.models.data_source import DataSource


class DataSourceActivateSerializer(serializers.Serializer):
    """Serializer for activating/deactivating a data source."""
    is_active = serializers.BooleanField(required=True)


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
