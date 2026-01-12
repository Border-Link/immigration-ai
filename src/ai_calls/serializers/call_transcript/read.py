from rest_framework import serializers
from ai_calls.models.call_transcript import CallTranscript


class CallTranscriptSerializer(serializers.ModelSerializer):
    """Serializer for reading call transcript."""
    
    class Meta:
        model = CallTranscript
        fields = [
            'id',
            'turn_number',
            'turn_type',
            'text',
            'speech_confidence',
            'ai_model',
            'guardrails_triggered',
            'guardrails_action',
            'timestamp',
            'duration_seconds',
        ]
        read_only_fields = fields
