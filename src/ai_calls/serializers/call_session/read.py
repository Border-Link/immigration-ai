from rest_framework import serializers
from ai_calls.models.call_session import CallSession


class CallSessionSerializer(serializers.ModelSerializer):
    """Serializer for reading call session."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    summary_id = serializers.UUIDField(source='summary.id', read_only=True, allow_null=True)
    parent_session_id = serializers.UUIDField(source='parent_session.id', read_only=True, allow_null=True)
    
    class Meta:
        model = CallSession
        fields = [
            'id',
            'case_id',
            'user_id',
            'status',
            'created_at',
            'ready_at',
            'started_at',
            'ended_at',
            'duration_seconds',
            'context_version',
            'context_hash',
            'webrtc_session_id',
            'warnings_count',
            'refusals_count',
            'escalated',
            'summary_id',
            'retry_count',
            'parent_session_id',
            'version',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'ready_at',
            'started_at',
            'ended_at',
            'duration_seconds',
            'context_version',
            'context_hash',
            'webrtc_session_id',
            'warnings_count',
            'refusals_count',
            'escalated',
            'summary_id',
            'retry_count',
            'parent_session_id',
            'version',
            'updated_at',
        ]
