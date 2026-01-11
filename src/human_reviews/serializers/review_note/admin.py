"""
Admin Serializers for ReviewNote Management

Serializers for admin review note management operations.
"""
from rest_framework import serializers


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
