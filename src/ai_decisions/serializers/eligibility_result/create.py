from rest_framework import serializers
from immigration_cases.selectors.case_selector import CaseSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultCreateSerializer(serializers.Serializer):
    """Serializer for creating an eligibility result."""
    
    case_id = serializers.UUIDField(required=True)
    visa_type_id = serializers.UUIDField(required=True)
    rule_version_id = serializers.UUIDField(required=True)
    outcome = serializers.ChoiceField(choices=EligibilityResult.OUTCOME_CHOICES, required=True)
    confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, default=0.0)
    reasoning_summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    missing_facts = serializers.JSONField(required=False, allow_null=True)

    def validate_case_id(self, value):
        """Validate case exists."""
        try:
            case = CaseSelector.get_by_id(value)
            if not case:
                raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        return value

    def validate_visa_type_id(self, value):
        """Validate visa type exists."""
        try:
            visa_type = VisaTypeSelector.get_by_id(value)
            if not visa_type:
                raise serializers.ValidationError(f"Visa type with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Visa type with ID '{value}' not found.")
        return value

    def validate_rule_version_id(self, value):
        """Validate rule version exists."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(value)
            if not rule_version:
                raise serializers.ValidationError(f"Rule version with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Rule version with ID '{value}' not found.")
        return value

