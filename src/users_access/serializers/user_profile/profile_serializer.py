from rest_framework import serializers
from users_access.models.user_profile import UserProfile
from users_access.selectors.country_selector import CountrySelector
from users_access.selectors.state_province_selector import StateProvinceSelector


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile with nested country and state."""
    nationality_code = serializers.CharField(source='nationality.code', read_only=True)
    nationality_name = serializers.CharField(source='nationality.name', read_only=True)
    state_province_code = serializers.CharField(source='state_province.code', read_only=True, allow_null=True)
    state_province_name = serializers.CharField(source='state_province.name', read_only=True, allow_null=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'nationality',
            'nationality_code',
            'nationality_name',
            'state_province',
            'state_province_code',
            'state_province_name',
            'date_of_birth',
            'consent_given',
            'consent_timestamp',
            'avatar',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'consent_timestamp']


class UserProfileUpdateSerializer(serializers.Serializer):
    """Comprehensive serializer for updating all user profile fields."""
    first_name = serializers.CharField(required=False, max_length=255, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(required=False, max_length=255, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    country_code = serializers.CharField(required=False, max_length=2, allow_blank=True, allow_null=True)
    state_code = serializers.CharField(required=False, max_length=10, allow_blank=True, allow_null=True)
    consent_given = serializers.BooleanField(required=False, allow_null=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    def validate_first_name(self, value):
        if value:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("First name cannot be empty.")
        return value

    def validate_last_name(self, value):
        if value:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Last name cannot be empty.")
        return value

    def validate_country_code(self, value):
        if value:
            value = value.strip().upper()
            country = CountrySelector.get_by_code(value)
            if not country:
                raise serializers.ValidationError(f"Country with code '{value}' not found.")
            if not country.is_active:
                raise serializers.ValidationError(f"Country '{value}' is not active.")
        return value

    def validate_state_code(self, value):
        if value:
            value = value.strip().upper()
        return value

    def validate_avatar(self, value):
        if value:
            from main_system.utils import image_processor as img_processor
            target_size_kb = 500
            image_quality = 85
            image_format = "webp"
            return img_processor.ImageProcessor(value, target_size_kb, image_quality, image_format).process()
        return value

    def validate(self, attrs):
        country_code = attrs.get('country_code')
        state_code = attrs.get('state_code')

        if state_code and country_code:
            country = CountrySelector.get_by_code(country_code)
            if not country:
                raise serializers.ValidationError({
                    'country_code': f"Country with code '{country_code}' not found."
                })
            if not country.has_states:
                raise serializers.ValidationError({
                    'state_code': f"Country '{country_code}' does not have states/provinces."
                })

            state = StateProvinceSelector.get_by_code(country_code, state_code)
            if not state:
                raise serializers.ValidationError({
                    'state_code': f"State/Province '{state_code}' not found for country '{country_code}'."
                })
            if not state.is_active:
                raise serializers.ValidationError({
                    'state_code': f"State/Province '{state_code}' is not active."
                })
        elif state_code and not country_code:
            raise serializers.ValidationError({
                'country_code': "Country code is required when state code is provided."
            })

        return attrs

