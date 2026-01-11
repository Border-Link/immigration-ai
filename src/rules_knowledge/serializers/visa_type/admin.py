"""
Admin Serializers for VisaType Management

Serializers for admin visa type management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import (
    BaseAdminListQuerySerializer,
    ActivateSerializer as BaseActivateSerializer
)


class VisaTypeAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating VisaTypeAdminListAPI query parameters."""
    
    jurisdiction = serializers.CharField(required=False, allow_null=True, max_length=10)
    is_active = serializers.BooleanField(required=False, allow_null=True)
    code = serializers.CharField(required=False, allow_null=True, max_length=50)


class VisaTypeActivateSerializer(BaseActivateSerializer):
    """Serializer for activating/deactivating a visa type."""
    pass


class BulkVisaTypeOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa type operations."""
    visa_type_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'activate',
        'deactivate',
        'delete',
    ])
