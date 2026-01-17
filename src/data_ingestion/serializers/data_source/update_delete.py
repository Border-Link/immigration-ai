from rest_framework import serializers
from data_ingestion.services.data_source_service import DataSourceService


class DataSourceUpdateSerializer(serializers.Serializer):
    """Serializer for updating a data source."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    name = serializers.CharField(required=False, max_length=255)
    base_url = serializers.URLField(required=False, max_length=500)
    crawl_frequency = serializers.CharField(required=False, max_length=50)
    is_active = serializers.BooleanField(required=False)

    def validate_base_url(self, value):
        """Validate base URL is unique if provided."""
        if value:
            existing = DataSourceService.get_by_base_url(value)
            if existing and existing.id != self.context.get('data_source_id'):
                raise serializers.ValidationError("A data source with this base URL already exists.")
        return value


class DataSourceIngestionTriggerSerializer(serializers.Serializer):
    """Serializer for triggering ingestion."""
    
    async_task = serializers.BooleanField(required=False, default=True)

