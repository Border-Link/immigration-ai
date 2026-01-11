"""
Admin Serializers for CaseFact Management

Serializers for admin case fact management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from immigration_cases.models.case_fact import CaseFact


class CaseFactAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating CaseFactAdminListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    fact_key = serializers.CharField(required=False, allow_null=True, max_length=255)
    source = serializers.ChoiceField(choices=CaseFact.SOURCE_CHOICES, required=False, allow_null=True)


class CaseFactAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to CaseFact."""
    
    class Meta:
        model = CaseFact
        fields = ['fact_value', 'source']


class BulkCaseFactOperationSerializer(serializers.Serializer):
    """Serializer for bulk case fact operations."""
    
    case_fact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'update_source',
    ])
    source = serializers.ChoiceField(
        choices=CaseFact.SOURCE_CHOICES,
        required=False,
        allow_null=True
    )
