from rest_framework import serializers


class DocumentCheckUpdateSerializer(serializers.Serializer):
    """Serializer for updating a document check."""
    
    result = serializers.ChoiceField(
        choices=['passed', 'failed', 'warning', 'pending'],
        required=False
    )
    details = serializers.JSONField(required=False, allow_null=True)
    performed_by = serializers.CharField(required=False, max_length=50, allow_null=True, allow_blank=True)


class DocumentCheckDeleteSerializer(serializers.Serializer):
    """Serializer for deleting a document check."""
    
    id = serializers.UUIDField(required=True)

