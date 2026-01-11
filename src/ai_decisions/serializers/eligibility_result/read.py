from rest_framework import serializers
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultListQuerySerializer(serializers.Serializer):
    """Serializer for validating EligibilityResultListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class EligibilityResultSerializer(serializers.ModelSerializer):
    """Serializer for EligibilityResult model."""
    
    class Meta:
        model = EligibilityResult
        fields = [
            'id',
            'case',
            'visa_type',
            'rule_version',
            'outcome',
            'confidence',
            'reasoning_summary',
            'missing_facts',
            'ai_reasoning_available',
            'requires_human_review',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class EligibilityResultListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing eligibility results."""
    
    class Meta:
        model = EligibilityResult
        fields = [
            'id',
            'case',
            'visa_type',
            'outcome',
            'confidence',
            'requires_human_review',
            'created_at',
        ]
        read_only_fields = '__all__'
