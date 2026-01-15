"""
Admin Serializers for User Management

Serializers for admin user management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from users_access.models.user import User
from users_access.models.notification import Notification


class UserAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating UserAdminListAPI query parameters."""
    
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, allow_null=True)
    is_verified = serializers.BooleanField(required=False, allow_null=True)
    email = serializers.CharField(required=False, allow_null=True, max_length=255)
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects and boolean values."""
        # Parse boolean strings before calling super
        if 'is_active' in data and data.get('is_active') is not None:
            if isinstance(data['is_active'], str):
                data['is_active'] = data['is_active'].lower() == 'true'
        if 'is_verified' in data and data.get('is_verified') is not None:
            if isinstance(data['is_verified'], str):
                data['is_verified'] = data['is_verified'].lower() == 'true'
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


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
        read_only_fields = (
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
        )
    
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
        read_only_fields = (
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
        )
    
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


class UserProfileAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating UserProfileAdminListAPI query parameters."""
    
    user_id = serializers.UUIDField(required=False, allow_null=True)
    nationality = serializers.CharField(required=False, allow_null=True, max_length=10)
    consent_given = serializers.BooleanField(required=False, allow_null=True)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects and boolean values."""
        if 'date_from' in data and isinstance(data['date_from'], str):
            parsed = parse_datetime(data['date_from'])
            if parsed:
                data['date_from'] = parsed
        if 'date_to' in data and isinstance(data['date_to'], str):
            parsed = parse_datetime(data['date_to'])
            if parsed:
                data['date_to'] = parsed
        if 'consent_given' in data and data['consent_given'] is not None:
            if isinstance(data['consent_given'], str):
                data['consent_given'] = data['consent_given'].lower() == 'true'
        return super().to_internal_value(data)


class NotificationAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating NotificationAdminListAPI query parameters."""
    
    user_id = serializers.UUIDField(required=False, allow_null=True)
    notification_type = serializers.ChoiceField(choices=Notification.TYPE_CHOICES, required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=Notification.PRIORITY_CHOICES, required=False, allow_null=True)
    is_read = serializers.BooleanField(required=False, allow_null=True)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects and boolean values."""
        if 'date_from' in data and isinstance(data['date_from'], str):
            parsed = parse_datetime(data['date_from'])
            if parsed:
                data['date_from'] = parsed
        if 'date_to' in data and isinstance(data['date_to'], str):
            parsed = parse_datetime(data['date_to'])
            if parsed:
                data['date_to'] = parsed
        if 'is_read' in data and data['is_read'] is not None:
            if isinstance(data['is_read'], str):
                data['is_read'] = data['is_read'].lower() == 'true'
        return super().to_internal_value(data)
