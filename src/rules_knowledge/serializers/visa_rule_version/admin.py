"""
Admin Serializers for VisaRuleVersion Management

Serializers for admin visa rule version management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class VisaRuleVersionPublishSerializer(serializers.Serializer):
    """Serializer for publishing/unpublishing a visa rule version."""
    is_published = serializers.BooleanField(required=True)


class VisaRuleVersionUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa rule version fields."""
    effective_from = serializers.DateTimeField(required=False)
    effective_to = serializers.DateTimeField(required=False, allow_null=True)
    is_published = serializers.BooleanField(required=False)
    source_document_version_id = serializers.UUIDField(required=False, allow_null=True)


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
