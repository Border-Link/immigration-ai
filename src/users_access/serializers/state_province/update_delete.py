from rest_framework import serializers
from users_access.selectors.state_province_selector import StateProvinceSelector
from users_access.models.state_province import StateProvince


class StateProvinceUpdateSerializer(serializers.Serializer):
    """Serializer for updating a state/province."""
    name = serializers.CharField(required=False, max_length=200)
    has_nomination_program = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_name(self, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("State/province name cannot be empty.")
            if len(value) < 2:
                raise serializers.ValidationError("State/province name must be at least 2 characters.")
        return value


class StateProvinceDeleteSerializer(serializers.Serializer):
    """Serializer for validating state/province deletion."""
    id = serializers.UUIDField(required=True)

    def validate_id(self, value):
        try:
            StateProvinceSelector.get_by_id(value)
        except StateProvince.DoesNotExist:
            raise serializers.ValidationError(f"State/province with ID '{value}' not found.")
        return value

