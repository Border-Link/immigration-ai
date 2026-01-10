"""
Admin Serializers for User Management

Serializers for admin user management operations.
"""
from rest_framework import serializers
from users_access.models.user import User


class UserAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing users in admin view."""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'is_active',
            'is_verified',
            'is_staff',
            'is_superuser',
            'login_count',
            'last_assigned_at',
            'created_at',
            'updated_at',
            'profile',
        ]
        read_only_fields = '__all__'
    
    def get_profile(self, obj):
        """Get profile information if exists."""
        try:
            profile = obj.profile
            return {
                'id': str(profile.id),
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'nationality': profile.nationality.code if profile.nationality else None,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            }
        except Exception:
            return None


class UserAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user view in admin."""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'is_active',
            'is_verified',
            'is_staff',
            'is_superuser',
            'login_count',
            'last_assigned_at',
            'created_at',
            'updated_at',
            'profile',
        ]
        read_only_fields = '__all__'
    
    def get_profile(self, obj):
        """Get full profile information."""
        try:
            profile = obj.profile
            return {
                'id': str(profile.id),
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'nationality': profile.nationality.code if profile.nationality else None,
                'state_province': profile.state_province.code if profile.state_province else None,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                'consent_given': profile.consent_given,
                'consent_timestamp': profile.consent_timestamp.isoformat() if profile.consent_timestamp else None,
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
            }
        except Exception:
            return None


class UserAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating user in admin."""
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    is_active = serializers.BooleanField(required=False)
    is_verified = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)


class UserSuspendSerializer(serializers.Serializer):
    """Serializer for suspending a user."""
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    suspended_until = serializers.DateTimeField(required=False, allow_null=True)


class UserVerifySerializer(serializers.Serializer):
    """Serializer for verifying/unverifying a user."""
    is_verified = serializers.BooleanField(required=True)


class BulkUserOperationSerializer(serializers.Serializer):
    """Serializer for bulk user operations."""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'activate',
        'deactivate',
        'verify',
        'unverify',
        'delete',
        'promote_to_reviewer',
        'demote_from_reviewer',
    ])
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class AdminPasswordResetSerializer(serializers.Serializer):
    """Serializer for admin password reset."""
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        max_length=128,
        write_only=True
    )
    send_email = serializers.BooleanField(default=False)


class UserRoleUpdateSerializer(serializers.Serializer):
    """Serializer for updating user role."""
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
