from rest_framework import serializers
from data_ingestion.models.data_source import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    """Serializer for reading data source data."""
    
    class Meta:
        model = DataSource
        fields = [
            'id',
            'name',
            'base_url',
            'jurisdiction',
            'is_active',
            'crawl_frequency',
            'last_fetched_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_fetched_at']


class DataSourceListSerializer(serializers.ModelSerializer):
    """Serializer for listing data sources."""
    
    class Meta:
        model = DataSource
        fields = [
            'id',
            'name',
            'base_url',
            'jurisdiction',
            'is_active',
            'last_fetched_at',
        ]

