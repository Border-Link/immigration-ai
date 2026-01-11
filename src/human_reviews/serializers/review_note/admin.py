"""
Admin Serializers for ReviewNote Management

Serializers for admin review note management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class ReviewNoteAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    review_id = serializers.UUIDField(required=False, allow_null=True)
    is_internal = serializers.BooleanField(required=False, allow_null=True)

    def to_internal_value(self, data):
        """Parse string dates to datetime objects and boolean values."""
        # Parse boolean strings before calling super
        if 'is_internal' in data and data.get('is_internal') is not None:
            if isinstance(data['is_internal'], str):
                data['is_internal'] = data['is_internal'].lower() == 'true'
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


class ReviewNoteAdminUpdateSerializer(serializers.Serializer):
    """Serializer for admin review note updates."""
    note = serializers.CharField(required=False)
    is_internal = serializers.BooleanField(required=False)


class BulkReviewNoteOperationSerializer(serializers.Serializer):
    """Serializer for bulk review note operations."""
    review_note_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'set_internal',
        'set_public',
    ])
