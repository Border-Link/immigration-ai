from rest_framework import serializers


class CallSessionUpdateSerializer(serializers.Serializer):
    """Serializer for updating call session."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
