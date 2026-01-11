"""
Admin Serializers for VisaRequirement Management

Serializers for admin visa requirement management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class VisaRequirementAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating VisaRequirementAdminListAPI query parameters."""
    
    rule_version_id = serializers.UUIDField(required=False, allow_null=True)
    rule_type = serializers.CharField(required=False, allow_null=True, max_length=50)
    is_mandatory = serializers.BooleanField(required=False, allow_null=True)
    requirement_code = serializers.CharField(required=False, allow_null=True, max_length=100)
    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    jurisdiction = serializers.CharField(required=False, allow_null=True, max_length=10)


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
