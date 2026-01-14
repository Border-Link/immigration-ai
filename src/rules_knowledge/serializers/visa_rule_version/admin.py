"""
Admin Serializers for VisaRuleVersion Management

Serializers for admin visa rule version management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from rules_knowledge.models.visa_rule_version import VisaRuleVersion


class VisaRuleVersionAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating VisaRuleVersionAdminListAPI query parameters."""

    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    is_published = serializers.BooleanField(required=False, allow_null=True)
    jurisdiction = serializers.CharField(required=False, allow_null=True, max_length=10)
    effective_from = serializers.DateTimeField(required=False, allow_null=True)
    effective_to = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        """Validate date ranges."""
        # Validate date_from <= date_to (from base class)
        attrs = super().validate(attrs)

        # Validate effective_from <= effective_to
        effective_from = attrs.get('effective_from')
        effective_to = attrs.get('effective_to')
        self.validate_date_range(
            effective_from,
            effective_to,
            field_name='effective_to'
        )

        return attrs

    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        # Parse effective date fields
        self.parse_datetime_string(data, 'effective_from')
        self.parse_datetime_string(data, 'effective_to')

        # Parse base class date fields
        return super().to_internal_value(data)


class VisaRuleVersionPublishSerializer(serializers.Serializer):
    """Serializer for publishing/unpublishing a visa rule version."""
    is_published = serializers.BooleanField(required=True)
    version = serializers.IntegerField(
        required=False,
        help_text="Expected version number for optimistic locking. If provided, publish will fail if version doesn't match."
    )


class VisaRuleVersionUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa rule version fields."""
    effective_from = serializers.DateTimeField(required=False)
    effective_to = serializers.DateTimeField(required=False, allow_null=True)
    is_published = serializers.BooleanField(required=False)
    source_document_version_id = serializers.UUIDField(required=False, allow_null=True)
    version = serializers.IntegerField(
        required=False,
        help_text="Expected version number for optimistic locking. If provided, update will fail if version doesn't match."
    )

    def validate(self, attrs):
        """Validate effective_from <= effective_to."""
        effective_from = attrs.get('effective_from')
        effective_to = attrs.get('effective_to')
        if effective_from and effective_to and effective_to < effective_from:
            raise serializers.ValidationError({
                'effective_to': 'End date cannot be before start date.'
            })
        return attrs


class BulkVisaRuleVersionOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa rule version operations."""
    rule_version_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'publish',
        'unpublish',
        'delete',
    ])
