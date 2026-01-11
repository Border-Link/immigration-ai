"""
Base Admin Serializers

Base classes and mixins for admin serializers to reduce code duplication.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class DateRangeMixin:
    """
    Mixin for date range validation.
    
    Provides common date range validation logic for admin list query serializers.
    Child classes should define date field names (e.g., 'date_from', 'date_to').
    """
    
    def validate_date_range(self, date_from, date_to, field_name='date_to'):
        """
        Validate that end date is not before start date.
        
        Args:
            date_from: Start date
            date_to: End date
            field_name: Name of the end date field for error message
            
        Raises:
            ValidationError: If date_to < date_from
        """
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                field_name: 'End date cannot be before start date.'
            })
    
    def parse_datetime_string(self, data, field_name):
        """
        Parse datetime string to datetime object if needed.
        
        Args:
            data: Data dictionary
            field_name: Name of the datetime field to parse
        """
        if field_name in data and isinstance(data[field_name], str):
            parsed = parse_datetime(data[field_name])
            if parsed:
                data[field_name] = parsed


class PaginationMixin:
    """
    Mixin for pagination fields.
    
    Provides common pagination fields (page, page_size) for admin list query serializers.
    """
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class BaseAdminListQuerySerializer(DateRangeMixin, PaginationMixin, serializers.Serializer):
    """
    Base class for admin list query serializers.
    
    Provides common functionality:
    - Date range validation (date_from, date_to)
    - Pagination fields (page, page_size)
    - Datetime string parsing
    
    Child classes should:
    - Add module-specific filter fields
    - Override validate() to call validate_date_range() for each date range pair
    - Override to_internal_value() to parse datetime strings
    """
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        self.validate_date_range(
            attrs.get('date_from'),
            attrs.get('date_to'),
            field_name='date_to'
        )
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        self.parse_datetime_string(data, 'date_from')
        self.parse_datetime_string(data, 'date_to')
        return super().to_internal_value(data)


class ActivateSerializer(serializers.Serializer):
    """
    Reusable serializer for activate/deactivate operations.
    
    Used for simple activate/deactivate endpoints that only need an is_active boolean.
    """
    is_active = serializers.BooleanField(required=True)
