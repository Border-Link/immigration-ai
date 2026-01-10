"""
Admin Serializers for ParsedRule Management

Serializers for admin parsed rule management operations.
"""
from rest_framework import serializers
from data_ingestion.models.parsed_rule import ParsedRule


class ParsedRuleAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating parsed rule in admin."""
    status = serializers.ChoiceField(choices=ParsedRule.STATUS_CHOICES, required=False)
    confidence_score = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    description = serializers.CharField(required=False, allow_blank=True)
    source_excerpt = serializers.CharField(required=False, allow_blank=True)


class BulkParsedRuleOperationSerializer(serializers.Serializer):
    """Serializer for bulk parsed rule operations."""
    rule_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'approve',
        'reject',
        'mark_pending',
    ])
