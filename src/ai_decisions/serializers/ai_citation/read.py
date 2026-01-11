from rest_framework import serializers
from ai_decisions.models.ai_citation import AICitation


class AICitationListQuerySerializer(serializers.Serializer):
    """Serializer for validating AICitationListAPI query parameters."""
    
    reasoning_log_id = serializers.UUIDField(required=False, allow_null=True)
    document_version_id = serializers.UUIDField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class AICitationSerializer(serializers.ModelSerializer):
    """Serializer for AICitation model."""
    
    class Meta:
        model = AICitation
        fields = [
            'id',
            'reasoning_log',
            'document_version',
            'excerpt',
            'relevance_score',
            'created_at',
        ]
        read_only_fields = '__all__'


class AICitationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing AI citations."""
    
    class Meta:
        model = AICitation
        fields = [
            'id',
            'reasoning_log',
            'document_version',
            'relevance_score',
            'created_at',
        ]
        read_only_fields = '__all__'
