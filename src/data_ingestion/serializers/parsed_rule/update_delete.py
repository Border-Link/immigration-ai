from rest_framework import serializers


class ParsedRuleUpdateSerializer(serializers.Serializer):
    """Serializer for updating a parsed rule."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    status = serializers.ChoiceField(
        choices=['pending', 'approved', 'rejected', 'needs_revision'],
        required=False
    )
    description = serializers.CharField(required=False, allow_blank=True)
    extracted_logic = serializers.JSONField(required=False)
    confidence_score = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)

    def validate_status(self, value):
        """Validate status transition."""
        # Add business logic for status transitions if needed
        return value

    def validate_confidence_score(self, value):
        """Validate confidence score range."""
        if value is not None and (value < 0.0 or value > 1.0):
            raise serializers.ValidationError("Confidence score must be between 0.0 and 1.0")
        return value


class ParsedRuleStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating parsed rule status."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    status = serializers.ChoiceField(
        choices=['pending', 'approved', 'rejected', 'needs_revision'],
        required=True
    )

