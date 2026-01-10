"""
Admin Serializers for DocumentDiff Management

Serializers for admin document diff management operations.
"""
from rest_framework import serializers


class BulkDocumentDiffOperationSerializer(serializers.Serializer):
    """Serializer for bulk document diff operations."""
    diff_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
