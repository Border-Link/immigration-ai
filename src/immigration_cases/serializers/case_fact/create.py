from rest_framework import serializers
from immigration_cases.models.case_fact import CaseFact
from immigration_cases.selectors.case_selector import CaseSelector


class CaseFactCreateSerializer(serializers.Serializer):
    """Serializer for creating a case fact."""
    
    case_id = serializers.UUIDField(required=True)
    fact_key = serializers.CharField(required=True, max_length=255)
    fact_value = serializers.JSONField(required=True)
    source = serializers.ChoiceField(choices=CaseFact.SOURCE_CHOICES, required=False, default='user')

    def validate_case_id(self, value):
        """Validate case exists."""
        try:
            case = CaseSelector.get_by_id(value)
            if not case:
                raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        return value

    def validate_fact_key(self, value):
        """Validate fact key."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Fact key cannot be empty.")
        return value

