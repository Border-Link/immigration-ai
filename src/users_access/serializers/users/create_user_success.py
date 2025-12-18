from rest_framework import serializers
from users_access.models.user import User
from helpers import fields as input_fields

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User - gets names from profile."""
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            input_fields.ID,
            input_fields.EMAIL,
            input_fields.FIRST_NAME,
            input_fields.LAST_NAME,
            'full_name',
            input_fields.IS_ACTIVE,
            input_fields.IS_SUPERUSER,
            input_fields.IS_STAFF,
            input_fields.CREATED_AT,
            input_fields.UPDATED_AT,
        )

        read_only_fields = (
            input_fields.ID,
            input_fields.IS_ACTIVE,
            input_fields.IS_SUPERUSER,
            input_fields.IS_STAFF,
            input_fields.CREATED_AT,
            input_fields.UPDATED_AT,
        )

    def get_first_name(self, obj):
        """Get first name from profile."""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.first_name
        return None

    def get_last_name(self, obj):
        """Get last name from profile."""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.last_name
        return None

    def get_full_name(self, obj):
        """Get full name from profile."""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.full_name
        return None


class WhoAmISerializer(serializers.ModelSerializer):
    """Serializer for whoami endpoint - gets names from profile."""
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            input_fields.ID,
            input_fields.EMAIL,
            input_fields.FIRST_NAME,
            input_fields.LAST_NAME,
            'full_name',
            input_fields.IS_ACTIVE,
        )

    def get_first_name(self, obj):
        """Get first name from profile."""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.first_name
        return None

    def get_last_name(self, obj):
        """Get last name from profile."""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.last_name
        return None

    def get_full_name(self, obj):
        """Get full name from profile."""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.full_name
        return None