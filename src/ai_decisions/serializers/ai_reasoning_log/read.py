from rest_framework import serializers
from ai_decisions.models.ai_reasoning_log import AIReasoningLog


class AIReasoningLogSerializer(serializers.ModelSerializer):
    """Serializer for AIReasoningLog model."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    case_status = serializers.CharField(source='case.status', read_only=True)
    
    class Meta:
        model = AIReasoningLog
        fields = [
            'id',
            'case_id',
            'case_status',
            'prompt',
            'response',
            'model_name',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = '__all__'


class AIReasoningLogListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing AI reasoning logs."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = AIReasoningLog
        fields = [
            'id',
            'case_id',
            'model_name',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = '__all__'
