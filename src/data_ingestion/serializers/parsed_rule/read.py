from rest_framework import serializers
from data_ingestion.models.parsed_rule import ParsedRule


class ParsedRuleSerializer(serializers.ModelSerializer):
    """Serializer for reading parsed rule data."""
    
    source_url = serializers.CharField(source='document_version.source_document.source_url', read_only=True)
    document_version_hash = serializers.CharField(source='document_version.content_hash', read_only=True)
    
    class Meta:
        model = ParsedRule
        fields = [
            'id',
            'document_version',
            'source_url',
            'document_version_hash',
            'visa_code',
            'rule_type',
            'extracted_logic',
            'description',
            'source_excerpt',
            'confidence_score',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ParsedRuleListSerializer(serializers.ModelSerializer):
    """Serializer for listing parsed rules."""
    
    class Meta:
        model = ParsedRule
        fields = [
            'id',
            'visa_code',
            'rule_type',
            'confidence_score',
            'status',
            'created_at',
        ]

