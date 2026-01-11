"""
Admin Serializers for Case Management

Serializers for admin case management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from immigration_cases.models.case import Case


class CaseAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating CaseAdminListAPI query parameters."""
    
    user_id = serializers.UUIDField(required=False, allow_null=True)
    jurisdiction = serializers.ChoiceField(choices=Case.JURISDICTION_CHOICES, required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Case.STATUS_CHOICES, required=False, allow_null=True)
    updated_date_from = serializers.DateTimeField(required=False, allow_null=True)
    updated_date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        # Validate date_from <= date_to (from base class)
        attrs = super().validate(attrs)
        
        # Validate updated_date_from <= updated_date_to
        updated_date_from = attrs.get('updated_date_from')
        updated_date_to = attrs.get('updated_date_to')
        self.validate_date_range(
            updated_date_from,
            updated_date_to,
            field_name='updated_date_to'
        )
        
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        # Parse updated_date fields
        self.parse_datetime_string(data, 'updated_date_from')
        self.parse_datetime_string(data, 'updated_date_to')
        
        # Parse base class date fields
        return super().to_internal_value(data)


class CaseAdminStatisticsQuerySerializer(serializers.Serializer):
    """Serializer for validating ImmigrationCasesStatisticsAPI query parameters."""
    
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
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        return super().to_internal_value(data)


class CaseAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to Case."""
    
    version = serializers.IntegerField(required=True, help_text="Current version of the case for optimistic locking")
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, help_text="Reason for the update")
    
    class Meta:
        model = Case
        fields = ['status', 'jurisdiction', 'version', 'reason']


class BulkCaseOperationSerializer(serializers.Serializer):
    """Serializer for bulk case operations."""
    
    case_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'update_status',
        'delete',
        'archive',
    ])
    status = serializers.ChoiceField(
        choices=Case.STATUS_CHOICES,
        required=False,
        allow_null=True
    )
    jurisdiction = serializers.ChoiceField(
        choices=Case.JURISDICTION_CHOICES,
        required=False,
        allow_null=True
    )
