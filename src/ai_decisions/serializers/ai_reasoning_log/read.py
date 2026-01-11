from rest_framework import serializers
from ai_decisions.models.ai_reasoning_log import AIReasoningLog


class AIReasoningLogListQuerySerializer(serializers.Serializer):
    """Serializer for validating AIReasoningLogListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    model_name = serializers.CharField(required=False, allow_null=True, max_length=100)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class AIReasoningLogSerializer(serializers.ModelSerializer):
    """Serializer for AIReasoningLog model."""
    
    class Meta:
        model = AIReasoningLog
        fields = [
            'id',
            'case',
            'model_name',
            'prompt',
            'response',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = '__all__'


class AIReasoningLogListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing AI reasoning logs."""
    
    class Meta:
        model = AIReasoningLog
        fields = [
            'id',
            'case',
            'model_name',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = '__all__'
