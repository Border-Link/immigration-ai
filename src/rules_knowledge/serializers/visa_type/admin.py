"""
Admin Serializers for VisaType Management

Serializers for admin visa type management operations.
"""
from rest_framework import serializers


class VisaTypeActivateSerializer(serializers.Serializer):
    """Serializer for activating/deactivating a visa type."""
    is_active = serializers.BooleanField(required=True)


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
