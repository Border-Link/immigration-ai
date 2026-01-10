"""
Admin Serializers for VisaDocumentRequirement Management

Serializers for admin visa document requirement management operations.
"""
from rest_framework import serializers


class VisaDocumentRequirementUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa document requirement fields."""
    mandatory = serializers.BooleanField(required=False)
    conditional_logic = serializers.JSONField(required=False, allow_null=True)


class BulkVisaDocumentRequirementOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa document requirement operations."""
    document_requirement_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'set_mandatory',
        'set_optional',
        'delete',
    ])
