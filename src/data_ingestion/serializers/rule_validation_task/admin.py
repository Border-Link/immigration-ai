"""
Admin Serializers for RuleValidationTask Management

Serializers for admin rule validation task management operations.
"""
from rest_framework import serializers
from data_ingestion.models.rule_validation_task import RuleValidationTask


class RuleValidationTaskAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating rule validation task in admin."""
    status = serializers.ChoiceField(choices=RuleValidationTask.STATUS_CHOICES, required=False)
    reviewer_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    assigned_to = serializers.UUIDField(required=False, allow_null=True)


class BulkRuleValidationTaskOperationSerializer(serializers.Serializer):
    """Serializer for bulk rule validation task operations."""
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'assign',
        'approve',
        'reject',
        'mark_pending',
    ])
    assigned_to = serializers.UUIDField(required=False, allow_null=True)
