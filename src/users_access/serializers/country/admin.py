"""
Admin Serializers for Country Management

Serializers for admin country management operations.
"""
from rest_framework import serializers


class CountryActivateSerializer(serializers.Serializer):
    """Serializer for activating/deactivating a country."""
    is_active = serializers.BooleanField(required=True)


class CountrySetJurisdictionSerializer(serializers.Serializer):
    """Serializer for setting country as jurisdiction."""
    is_jurisdiction = serializers.BooleanField(required=True)
