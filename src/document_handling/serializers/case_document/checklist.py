"""
Serializers for document checklist.
"""
from rest_framework import serializers


class DocumentChecklistSerializer(serializers.Serializer):
    """Serializer for document checklist response."""
    
    case_id = serializers.UUIDField(read_only=True)
    visa_type = serializers.DictField(read_only=True)
    rule_version = serializers.DictField(read_only=True)
    requirements = serializers.ListField(read_only=True)
    summary = serializers.DictField(read_only=True)
    error = serializers.CharField(required=False, allow_null=True)
