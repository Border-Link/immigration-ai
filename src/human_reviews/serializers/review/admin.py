"""
Admin Serializers for Review Management

Serializers for admin review management operations.
"""
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from human_reviews.models.review import Review


class ReviewAdminListQuerySerializer(serializers.Serializer):
    """Serializer for validating ReviewAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Review.STATUS_CHOICES, required=False, allow_null=True)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    assigned_date_from = serializers.DateTimeField(required=False, allow_null=True)
    assigned_date_to = serializers.DateTimeField(required=False, allow_null=True)
    completed_date_from = serializers.DateTimeField(required=False, allow_null=True)
    completed_date_to = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date ranges."""
        # Validate date_from <= date_to
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                'date_to': 'End date cannot be before start date.'
            })
        
        # Validate assigned_date_from <= assigned_date_to
        assigned_date_from = attrs.get('assigned_date_from')
        assigned_date_to = attrs.get('assigned_date_to')
        if assigned_date_from and assigned_date_to and assigned_date_to < assigned_date_from:
            raise serializers.ValidationError({
                'assigned_date_to': 'End date cannot be before start date.'
            })
        
        # Validate completed_date_from <= completed_date_to
        completed_date_from = attrs.get('completed_date_from')
        completed_date_to = attrs.get('completed_date_to')
        if completed_date_from and completed_date_to and completed_date_to < completed_date_from:
            raise serializers.ValidationError({
                'completed_date_to': 'End date cannot be before start date.'
            })
        
        return attrs
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects."""
        if 'date_from' in data and isinstance(data['date_from'], str):
            data['date_from'] = parse_datetime(data['date_from'])
        if 'date_to' in data and isinstance(data['date_to'], str):
            data['date_to'] = parse_datetime(data['date_to'])
        if 'assigned_date_from' in data and isinstance(data['assigned_date_from'], str):
            data['assigned_date_from'] = parse_datetime(data['assigned_date_from'])
        if 'assigned_date_to' in data and isinstance(data['assigned_date_to'], str):
            data['assigned_date_to'] = parse_datetime(data['assigned_date_to'])
        if 'completed_date_from' in data and isinstance(data['completed_date_from'], str):
            data['completed_date_from'] = parse_datetime(data['completed_date_from'])
        if 'completed_date_to' in data and isinstance(data['completed_date_to'], str):
            data['completed_date_to'] = parse_datetime(data['completed_date_to'])
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