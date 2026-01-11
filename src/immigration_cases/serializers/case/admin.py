"""
Admin Serializers for Case Management

Serializers for admin case management operations.
"""
from rest_framework import serializers
from immigration_cases.models.case import Case


class CaseAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to Case."""
    
    version = serializers.IntegerField(required=True, help_text="Current version of the case for optimistic locking")
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, help_text="Reason for the update")
    
    class Meta:
        model = Case
        fields = ['status', 'jurisdiction', 'version', 'reason']


class BulkCaseOperationSerializer(serializers.Serializer):
    """Serializer for bulk case operations."""
    
    case_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'update_status',
        'delete',
        'archive',
    ])
    status = serializers.ChoiceField(
        choices=Case.STATUS_CHOICES,
        required=False,
        allow_null=True
    )
    jurisdiction = serializers.ChoiceField(
        choices=Case.JURISDICTION_CHOICES,
        required=False,
        allow_null=True
    )
