from rest_framework import serializers
from users_access.selectors.country_selector import CountrySelector
from users_access.models.country import Country


class CountryUpdateSerializer(serializers.Serializer):
    """Serializer for updating a country."""
    code = serializers.CharField(required=False, allow_blank=True, max_length=10)
    name = serializers.CharField(required=False, max_length=200)
    has_states = serializers.BooleanField(required=False)
    is_jurisdiction = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_code(self, value):
        if value is not None:
            value = value.strip().upper()
            if not value:
                raise serializers.ValidationError("Country code cannot be empty.")
            if len(value) < 2:
                raise serializers.ValidationError("Country code must be at least 2 characters.")
        return value

    def validate_name(self, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Country name cannot be empty.")
            if len(value) < 2:
                raise serializers.ValidationError("Country name must be at least 2 characters.")
        return value


class CountryDeleteSerializer(serializers.Serializer):
    """Serializer for validating country deletion."""
    id = serializers.UUIDField(required=True)

