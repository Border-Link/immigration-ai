from rest_framework import serializers
from immigration_cases.models.case_status_history import CaseStatusHistory

class CaseStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for reading CaseStatusHistory data."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    
    class Meta:
        model = CaseStatusHistory
        fields = [
            'id',
            'case_id',
            'previous_status',
            'new_status',
            'changed_by_email',
            'reason',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields

class CaseStatusHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing CaseStatusHistory data."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    
    class Meta:
        model = CaseStatusHistory
        fields = [
            'id',
            'case_id',
            'previous_status',
            'new_status',
            'changed_by_email',
            'created_at',
        ]
        read_only_fields = fields
