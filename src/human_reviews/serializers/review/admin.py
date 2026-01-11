"""
Admin Serializers for Review Management

Serializers for admin review management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from human_reviews.models.review import Review


class ReviewAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating ReviewAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Review.STATUS_CHOICES, required=False, allow_null=True)
    assigned_date_from = serializers.DateTimeField(required=False, allow_null=True)
    assigned_date_to = serializers.DateTimeField(required=False, allow_null=True)
    completed_date_from = serializers.DateTimeField(required=False, allow_null=True)
    completed_date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        # Validate date_from <= date_to (from base class)
        attrs = super().validate(attrs)
        
        # Validate assigned_date_from <= assigned_date_to
        assigned_date_from = attrs.get('assigned_date_from')
        assigned_date_to = attrs.get('assigned_date_to')
        self.validate_date_range(
            assigned_date_from,
            assigned_date_to,
            field_name='assigned_date_to'
        )
        
        # Validate completed_date_from <= completed_date_to
        completed_date_from = attrs.get('completed_date_from')
        completed_date_to = attrs.get('completed_date_to')
        self.validate_date_range(
            completed_date_from,
            completed_date_to,
            field_name='completed_date_to'
        )
        
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        # Parse additional date fields
        self.parse_datetime_string(data, 'assigned_date_from')
        self.parse_datetime_string(data, 'assigned_date_to')
        self.parse_datetime_string(data, 'completed_date_from')
        self.parse_datetime_string(data, 'completed_date_to')
        
        # Parse base class date fields
        return super().to_internal_value(data)


class ReviewStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating review status."""
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'cancelled'],
        required=True
    )


class ReviewAssignSerializer(serializers.Serializer):
    """Serializer for assigning a reviewer."""
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    assignment_strategy = serializers.ChoiceField(
        choices=['round_robin', 'workload'],
        required=False,
        default='round_robin'
    )


class BulkReviewOperationSerializer(serializers.Serializer):
    """Serializer for bulk review operations."""
    review_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'assign',
        'complete',
        'cancel',
        'delete',
    ])
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    assignment_strategy = serializers.ChoiceField(
        choices=['round_robin', 'workload'],
        required=False,
        default='round_robin'
    )


class ReviewAdminUpdateSerializer(serializers.Serializer):
    """Serializer for admin review updates."""
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'cancelled'],
        required=False
    )
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    version = serializers.IntegerField(
        required=False,
        help_text="Expected version number for optimistic locking."
    )