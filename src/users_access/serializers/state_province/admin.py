"""
Admin Serializers for State/Province Management

Serializers for admin state/province management operations.
"""
from rest_framework import serializers


class StateProvinceActivateSerializer(serializers.Serializer):
    """Serializer for activating/deactivating a state/province."""
    is_active = serializers.BooleanField(required=True)
