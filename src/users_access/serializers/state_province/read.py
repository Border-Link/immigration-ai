from rest_framework import serializers
from users_access.models.state_province import StateProvince
from users_access.selectors.country_selector import CountrySelector


class StateProvinceSerializer(serializers.ModelSerializer):
    """Serializer for StateProvince model."""
    country_code = serializers.CharField(source='country.code', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model = StateProvince
        fields = [
            'id',
            'country',
            'country_code',
            'country_name',
            'code',
            'name',
            'has_nomination_program',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StateProvinceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for state/province lists."""
    country_code = serializers.CharField(source='country.code', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model = StateProvince
        fields = ['id', 'country_code', 'country_name', 'code', 'name', 'has_nomination_program']


class StateProvinceByCountrySerializer(serializers.Serializer):
    """Serializer for filtering states by country."""
    country_code = serializers.CharField(required=True, max_length=2)

    def validate_country_code(self, value):
        value = value.strip().upper()
        country = CountrySelector.get_by_code(value)
        if not country:
            raise serializers.ValidationError(f"Country with code '{value}' not found.")
        if not country.is_active:
            raise serializers.ValidationError(f"Country '{value}' is not active.")
        if not country.has_states:
            raise serializers.ValidationError(f"Country '{value}' does not have states/provinces.")
        return value

