"""
Admin Serializers for AICitation Management

Serializers for admin AI citation management operations.
"""
from rest_framework import serializers


class AICitationAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating AI citation in admin."""
    excerpt = serializers.CharField(required=False, allow_blank=True)
    relevance_score = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, allow_null=True)


class BulkAICitationOperationSerializer(serializers.Serializer):
    """Serializer for bulk AI citation operations."""
    citation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
