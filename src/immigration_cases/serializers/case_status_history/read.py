from rest_framework import serializers
from immigration_cases.models.case_status_history import CaseStatusHistory


class CaseStatusHistoryListQuerySerializer(serializers.Serializer):
    """Serializer for validating CaseStatusHistoryListAPI query parameters."""
    
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class CaseStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for CaseStatusHistory model."""
    
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = CaseStatusHistory
        fields = [
            'id',
            'case_id',
            'previous_status',
            'new_status',
            'changed_by',
            'changed_by_email',
            'reason',
            'metadata',
            'created_at',
        ]


class CaseStatusHistoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing case status history."""
    
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = CaseStatusHistory
        fields = [
            'id',
            'case_id',
            'previous_status',
            'new_status',
            'changed_by_email',
            'reason',
            'created_at',
        ]
