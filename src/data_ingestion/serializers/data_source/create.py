from rest_framework import serializers
from data_ingestion.selectors.data_source_selector import DataSourceSelector


class DataSourceCreateSerializer(serializers.Serializer):
    """Serializer for creating a data source."""
    
    name = serializers.CharField(required=True, max_length=255)
    base_url = serializers.URLField(required=True, max_length=500)
    jurisdiction = serializers.ChoiceField(
        choices=['UK', 'US', 'CA', 'AU'],
        required=True
    )
    crawl_frequency = serializers.CharField(
        required=False,
        default='daily',
        max_length=50
    )
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_base_url(self, value):
        """Validate base URL is unique."""
        existing = DataSourceSelector.get_by_base_url(value)
        if existing:
            raise serializers.ValidationError("A data source with this base URL already exists.")
        return value

