from rest_framework import serializers
from users_access.models.user import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User - gets names from profile."""
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            'full_name',
            "is_active",
            "is_superuser",
            "is_staff",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "is_active",
            "is_superuser",
            "is_staff",
            "created_at",
            "updated_at",
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
            first = (obj.profile.first_name or "").strip()
            last = (obj.profile.last_name or "").strip()
            full = " ".join([p for p in (first, last) if p])
            return full or None
        return None


class WhoAmISerializer(serializers.ModelSerializer):
    """Serializer for whoami endpoint - gets names from profile."""
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            'full_name',
            "is_active",
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
            first = (obj.profile.first_name or "").strip()
            last = (obj.profile.last_name or "").strip()
            full = " ".join([p for p in (first, last) if p])
            return full or None
        return None