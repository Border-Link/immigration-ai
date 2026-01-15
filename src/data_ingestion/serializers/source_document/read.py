from rest_framework import serializers
from data_ingestion.models.source_document import SourceDocument


class SourceDocumentSerializer(serializers.ModelSerializer):
    """Serializer for reading source document data."""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    data_source_jurisdiction = serializers.CharField(source='data_source.jurisdiction', read_only=True)
    
    class Meta:
        model = SourceDocument
        fields = [
            'id',
            'data_source',
            'data_source_name',
            'data_source_jurisdiction',
            'source_url',
            'fetched_at',
            'content_type',
            'http_status_code',
            'fetch_error',
        ]
        read_only_fields = ['id', 'fetched_at']


class SourceDocumentListSerializer(serializers.ModelSerializer):
    """Serializer for listing source documents."""
    
    class Meta:
        model = SourceDocument
        fields = [
            'id',
            'source_url',
            'fetched_at',
            'content_type',
            'http_status_code',
        ]

