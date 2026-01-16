from rest_framework import serializers
from human_reviews.models.decision_override import DecisionOverride


class DecisionOverrideSerializer(serializers.ModelSerializer):
    """Serializer for DecisionOverride model."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    original_result_id = serializers.UUIDField(source='original_result.id', read_only=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True, allow_null=True)
    
    class Meta:
        model = DecisionOverride
        fields = [
            'id',
            'case_id',
            'original_result_id',
            'overridden_outcome',
            'reason',
            'reviewer',
            'reviewer_email',
            'created_at',
        ]
        read_only_fields = (
            'id',
            'case_id',
            'original_result_id',
            'overridden_outcome',
            'reason',
            'reviewer',
            'reviewer_email',
            'created_at',
        )


class DecisionOverrideListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing decision overrides."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    original_result_id = serializers.UUIDField(source='original_result.id', read_only=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True, allow_null=True)
    
    class Meta:
        model = DecisionOverride
        fields = [
            'id',
            'case_id',
            'original_result_id',
            'overridden_outcome',
            'reviewer_email',
            'created_at',
        ]
        read_only_fields = (
            'id',
            'case_id',
            'original_result_id',
            'overridden_outcome',
            'reviewer_email',
            'created_at',
        )

