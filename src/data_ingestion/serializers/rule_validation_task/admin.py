"""
Admin Serializers for RuleValidationTask Management

Serializers for admin rule validation task management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from data_ingestion.models.rule_validation_task import RuleValidationTask


class RuleValidationTaskAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    status = serializers.CharField(required=False, allow_null=True)
    assigned_to = serializers.UUIDField(required=False, allow_null=True)
    sla_overdue = serializers.BooleanField(required=False, allow_null=True)

    def to_internal_value(self, data):
        """Parse string dates to datetime objects and boolean values."""
        data = data.copy()
        # Parse boolean strings before calling super
        if 'sla_overdue' in data and data.get('sla_overdue') is not None:
            if isinstance(data['sla_overdue'], str):
                data['sla_overdue'] = data['sla_overdue'].lower() == 'true'
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


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
