from rest_framework import serializers
from immigration_cases.selectors.case_selector import CaseSelector


class CallSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a call session."""
    
    case_id = serializers.UUIDField(required=True)
    parent_session_id = serializers.UUIDField(required=False, allow_null=True, help_text="Parent session ID if this is a retry")

    def validate_case_id(self, value):
        """Validate case exists."""
        try:
            case = CaseSelector.get_by_id(value)
            if not case:
                raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        return value
