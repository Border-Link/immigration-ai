from rest_framework import serializers


class VisaDocumentRequirementUpdateSerializer(serializers.Serializer):
    """Serializer for updating a visa document requirement."""
    
    mandatory = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)

