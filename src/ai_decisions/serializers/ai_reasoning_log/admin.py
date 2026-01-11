"""
Admin Serializers for AIReasoningLog Management

Serializers for admin AI reasoning log management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class AIReasoningLogAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating AIReasoningLogAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    model_name = serializers.CharField(required=False, allow_null=True, max_length=100)
    min_tokens = serializers.IntegerField(required=False, allow_null=True, min_value=0)


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
