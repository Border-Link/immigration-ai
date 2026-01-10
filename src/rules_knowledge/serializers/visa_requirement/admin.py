"""
Admin Serializers for VisaRequirement Management

Serializers for admin visa requirement management operations.
"""
from rest_framework import serializers


class VisaRequirementUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa requirement fields."""
    requirement_code = serializers.CharField(max_length=100, required=False)
    rule_type = serializers.ChoiceField(
        choices=[
            ('eligibility', 'Eligibility Requirement'),
            ('document', 'Document Requirement'),
            ('fee', 'Fee Information'),
            ('processing_time', 'Processing Time'),
            ('other', 'Other'),
        ],
        required=False
    )
    description = serializers.CharField(required=False, allow_blank=True)
    condition_expression = serializers.JSONField(required=False)
    is_mandatory = serializers.BooleanField(required=False)


class BulkVisaRequirementOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa requirement operations."""
    requirement_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'set_mandatory',
        'set_optional',
    ])
