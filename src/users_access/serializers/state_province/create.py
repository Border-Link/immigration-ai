from rest_framework import serializers
from users_access.selectors.country_selector import CountrySelector
from users_access.selectors.state_province_selector import StateProvinceSelector
from users_access.models.country import Country


class StateProvinceCreateSerializer(serializers.Serializer):
    """Serializer for creating a state/province."""
    country_id = serializers.UUIDField(required=True)
    code = serializers.CharField(required=True, max_length=10)
    name = serializers.CharField(required=True, max_length=200)
    has_nomination_program = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_country_id(self, value):
        try:
            country = CountrySelector.get_by_id(value)
            if not country.has_states:
                raise serializers.ValidationError(f"Country does not have states/provinces enabled.")
            # Store country object in context for use in validate method
            self.context['country'] = country
        except Country.DoesNotExist:
            raise serializers.ValidationError(f"Country with ID '{value}' not found.")
        return value

    def validate_code(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("State/province code cannot be empty.")
        if len(value) > 10:
            raise serializers.ValidationError("State/province code must be at most 10 characters.")
        return value

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("State/province name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("State/province name must be at least 2 characters.")
        return value

    def validate(self, attrs):
        country = self.context.get('country')
        state_code = attrs.get('code')
        
        if country and state_code:
            if StateProvinceSelector.code_exists(country.code, state_code):
                raise serializers.ValidationError({
                    'code': f"State/province with code '{state_code}' already exists for this country."
                })
        
        return attrs

