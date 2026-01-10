"""
Admin Serializers for AIReasoningLog Management

Serializers for admin AI reasoning log management operations.
"""
from rest_framework import serializers


class BulkAIReasoningLogOperationSerializer(serializers.Serializer):
    """Serializer for bulk AI reasoning log operations."""
    log_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
