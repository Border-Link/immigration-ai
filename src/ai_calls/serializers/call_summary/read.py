from rest_framework import serializers
from ai_calls.models.call_summary import CallSummary


class CallSummarySerializer(serializers.ModelSerializer):
    """Serializer for reading call summary."""
    
    class Meta:
        model = CallSummary
        fields = [
            'id',
            'summary_text',
            'key_questions',
            'action_items',
            'missing_documents',
            'suggested_next_steps',
            'total_turns',
            'total_duration_seconds',
            'topics_discussed',
            'attached_to_case',
            'created_at',
        ]
        read_only_fields = fields
