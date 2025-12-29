from rest_framework import serializers


class DocumentTypeUpdateSerializer(serializers.Serializer):
    """Serializer for updating a document type."""
    
    name = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

