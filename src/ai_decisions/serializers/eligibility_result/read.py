from rest_framework import serializers
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultListQuerySerializer(serializers.Serializer):
    """Serializer for validating EligibilityResultListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class EligibilityResultSerializer(serializers.ModelSerializer):
    """Serializer for EligibilityResult model."""

    requires_human_review = serializers.SerializerMethodField()
    
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
            'requires_human_review',
            'created_at',
            'updated_at',
        ]

        read_only_fields = (
            'id',
            'case',
            'visa_type',
            'rule_version',
            'outcome',
            'confidence',
            'reasoning_summary',
            'missing_facts',
            'requires_human_review',
            'created_at',
            'updated_at',
        )

    def get_requires_human_review(self, obj) -> bool:
        # Conservative: outcomes requiring review/missing facts are review-worthy.
        return obj.outcome in {'requires_review', 'missing_facts'}


class EligibilityResultListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing eligibility results."""

    requires_human_review = serializers.SerializerMethodField()
    
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
        read_only_fields = (
            'id',
            'case',
            'visa_type',
            'outcome',
            'confidence',
            'requires_human_review',
            'created_at',
        )

    def get_requires_human_review(self, obj) -> bool:
        return obj.outcome in {'requires_review', 'missing_facts'}
