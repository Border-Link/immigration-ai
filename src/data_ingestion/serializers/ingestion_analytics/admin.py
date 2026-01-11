"""
Admin Serializers for Ingestion Analytics

Serializers for admin ingestion analytics operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class ParsingCostAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for validating query parameters in cost analytics view."""
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    llm_model = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        """Validate that end date is not smaller than start date."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be smaller than start date.'
            })
        
        return attrs

    def to_internal_value(self, data):
        """Parse string dates to datetime objects."""
        if 'date_from' in data and data['date_from']:
            if isinstance(data['date_from'], str):
                parsed = parse_datetime(data['date_from'])
                if parsed:
                    data['date_from'] = parsed
        
        if 'date_to' in data and data['date_to']:
            if isinstance(data['date_to'], str):
                parsed = parse_datetime(data['date_to'])
                if parsed:
                    data['date_to'] = parsed
        
        return super().to_internal_value(data)
