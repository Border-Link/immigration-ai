"""
Admin Serializers for VisaRuleVersion Management

Serializers for admin visa rule version management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from rules_knowledge.models.visa_rule_version import VisaRuleVersion


class VisaRuleVersionAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating VisaRuleVersionAdminListAPI query parameters."""
    
    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    is_published = serializers.BooleanField(required=False, allow_null=True)
    jurisdiction = serializers.CharField(required=False, allow_null=True, max_length=10)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    effective_from = serializers.DateTimeField(required=False, allow_null=True)
    effective_to = serializers.DateTimeField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    
    def validate(self, attrs):
        """Validate date ranges."""
        # Validate date_from <= date_to
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        
        # Validate effective_from <= effective_to
        effective_from = attrs.get('effective_from')
        effective_to = attrs.get('effective_to')
        if effective_from and effective_to and effective_to < effective_from:
            raise serializers.ValidationError({
                'effective_to': 'End date cannot be before start date.'
            })
        
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        if 'effective_from' in data and isinstance(data['effective_from'], str):
            data['effective_from'] = parse_datetime(data['effective_from'])
        if 'effective_to' in data and isinstance(data['effective_to'], str):
            data['effective_to'] = parse_datetime(data['effective_to'])
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
