"""
Admin Serializers for ParsedRule Management

Serializers for admin parsed rule management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from data_ingestion.models.parsed_rule import ParsedRule


class ParsedRuleAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    status = serializers.CharField(required=False, allow_null=True)
    visa_code = serializers.CharField(required=False, allow_null=True)
    rule_type = serializers.CharField(required=False, allow_null=True)
    min_confidence = serializers.FloatField(required=False, allow_null=True, min_value=0.0, max_value=1.0)

    def to_internal_value(self, data):
        """Parse string dates to datetime objects and float values."""
        data = data.copy()
        # Parse float strings before calling super
        if 'min_confidence' in data and data.get('min_confidence'):
            if isinstance(data['min_confidence'], str):
                try:
                    data['min_confidence'] = float(data['min_confidence'])
                except (ValueError, TypeError):
                    pass
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


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
