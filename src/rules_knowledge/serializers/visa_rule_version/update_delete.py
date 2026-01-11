from rest_framework import serializers


class VisaRuleVersionUpdateSerializer(serializers.Serializer):
    """Serializer for updating a visa rule version."""
    
    effective_from = serializers.DateTimeField(required=False)
    effective_to = serializers.DateTimeField(required=False, allow_null=True)
    version = serializers.IntegerField(
        required=False,
        help_text="Expected version number for optimistic locking. If provided, update will fail if version doesn't match."
    )

