from django.db import transaction
from django.utils import timezone
from data_ingestion.models.rule_validation_task import RuleValidationTask
from data_ingestion.models.parsed_rule import ParsedRule


class RuleValidationTaskRepository:
    """Repository for RuleValidationTask write operations."""

    @staticmethod
    def create_validation_task(parsed_rule: ParsedRule, assigned_to=None,
                               sla_deadline=None, status: str = 'pending'):
        """Create a new validation task."""
        with transaction.atomic():
            task = RuleValidationTask.objects.create(
                parsed_rule=parsed_rule,
                assigned_to=assigned_to,
                status=status,
                sla_deadline=sla_deadline
            )
            task.full_clean()
            task.save()
            return task

    @staticmethod
    def update_validation_task(task, **fields):
        """Update validation task fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            if 'status' in fields and fields['status'] in ['approved', 'rejected', 'needs_revision']:
                task.reviewed_at = timezone.now()
            task.full_clean()
            task.save()
            return task

    @staticmethod
    def assign_reviewer(task, reviewer):
        """Assign a reviewer to the validation task."""
        with transaction.atomic():
            task.assigned_to = reviewer
            task.status = 'in_progress'
            task.full_clean()
            task.save()
            return task

    @staticmethod
    def delete_validation_task(task):
        """Delete a validation task."""
        with transaction.atomic():
            task.delete()
            return True
