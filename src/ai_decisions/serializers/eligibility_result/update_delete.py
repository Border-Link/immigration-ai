from rest_framework import serializers
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultUpdateSerializer(serializers.Serializer):
    """Serializer for updating an eligibility result."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    outcome = serializers.ChoiceField(choices=EligibilityResult.OUTCOME_CHOICES, required=False)
    confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    reasoning_summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    missing_facts = serializers.JSONField(required=False, allow_null=True)

