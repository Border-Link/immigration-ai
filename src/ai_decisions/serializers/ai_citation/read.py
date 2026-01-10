from rest_framework import serializers
from ai_decisions.models.ai_citation import AICitation


class AICitationSerializer(serializers.ModelSerializer):
    """Serializer for AICitation model."""
    
    reasoning_log_id = serializers.UUIDField(source='reasoning_log.id', read_only=True)
    case_id = serializers.UUIDField(source='reasoning_log.case.id', read_only=True)
    document_version_id = serializers.UUIDField(source='document_version.id', read_only=True)
    source_url = serializers.CharField(source='document_version.source_document.source_url', read_only=True)
    document_title = serializers.CharField(source='document_version.source_document.title', read_only=True, allow_null=True)
    
    class Meta:
        model = AICitation
        fields = [
            'id',
            'reasoning_log_id',
            'case_id',
            'document_version_id',
            'source_url',
            'document_title',
            'excerpt',
            'relevance_score',
            'created_at',
        ]
        read_only_fields = '__all__'


class AICitationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing AI citations."""
    
    reasoning_log_id = serializers.UUIDField(source='reasoning_log.id', read_only=True)
    source_url = serializers.CharField(source='document_version.source_document.source_url', read_only=True)
    
    class Meta:
        model = AICitation
        fields = [
            'id',
            'reasoning_log_id',
            'source_url',
            'relevance_score',
            'created_at',
        ]
        read_only_fields = '__all__'
