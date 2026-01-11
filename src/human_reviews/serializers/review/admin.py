"""
Admin Serializers for Review Management

Serializers for admin review management operations.
"""
from rest_framework import serializers


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
