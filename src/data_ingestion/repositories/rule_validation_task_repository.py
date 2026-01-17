from django.db import transaction
from django.utils import timezone
from django.db.models import F
from django.core.exceptions import ValidationError
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
                sla_deadline=sla_deadline,
                version=1,
                is_deleted=False,
            )
            task.full_clean()
            task.save()
            return task

    @staticmethod
    def update_validation_task(task: RuleValidationTask, version: int = None, **fields):
        """Update validation task fields with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(task, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in RuleValidationTask._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            now_ts = timezone.now()
            if "status" in update_fields and update_fields["status"] in ["approved", "rejected", "needs_revision"]:
                update_fields["reviewed_at"] = now_ts

            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = now_ts

            updated_count = RuleValidationTask.objects.filter(
                id=task.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = RuleValidationTask.objects.filter(id=task.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Validation task not found.")
                raise ValidationError(
                    f"Validation task was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return RuleValidationTask.objects.get(id=task.id)

    @staticmethod
    def assign_reviewer(task: RuleValidationTask, reviewer, version: int = None):
        """Assign a reviewer to the validation task with optimistic locking."""
        return RuleValidationTaskRepository.update_validation_task(
            task,
            version=version if version is not None else getattr(task, "version", None),
            assigned_to=reviewer,
            status="in_progress",
        )

    @staticmethod
    def soft_delete_validation_task(task: RuleValidationTask, version: int = None) -> RuleValidationTask:
        """Soft delete a validation task with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(task, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = RuleValidationTask.objects.filter(
                id=task.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = RuleValidationTask.objects.filter(id=task.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Validation task not found.")
                raise ValidationError(
                    f"Validation task was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return RuleValidationTask.objects.get(id=task.id)

    @staticmethod
    def delete_validation_task(task: RuleValidationTask, version: int = None):
        """
        Delete a validation task.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        RuleValidationTaskRepository.soft_delete_validation_task(task, version=version)
        return True
