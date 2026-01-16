"""
Serializers for AI Decisions Analytics Views

Serializers for validating query parameters in analytics endpoints.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class TokenUsageAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for validating TokenUsageAnalyticsAPI query parameters."""
    
    model_name = serializers.CharField(required=False, allow_null=True, max_length=100)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        # `request.query_params` is a (immutable) QueryDict; copy before mutation.
        data = data.copy()
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        return super().to_internal_value(data)


class CitationQualityAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for validating CitationQualityAnalyticsAPI query parameters."""
    
    min_relevance = serializers.FloatField(required=False, allow_null=True, min_value=0.0, max_value=1.0)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        # `request.query_params` is a (immutable) QueryDict; copy before mutation.
        data = data.copy()
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        return super().to_internal_value(data)
