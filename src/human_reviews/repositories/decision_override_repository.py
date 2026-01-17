from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from main_system.repositories.base import BaseRepositoryMixin
from human_reviews.models.decision_override import DecisionOverride
from immigration_cases.models.case import Case
from ai_decisions.models.eligibility_result import EligibilityResult
from django.conf import settings


class DecisionOverrideRepository:
    """Repository for DecisionOverride write operations."""

    @staticmethod
    def create_decision_override(case: Case, original_result: EligibilityResult,
                                 overridden_outcome: str, reason: str, reviewer=None):
        """Create a new decision override."""
        with transaction.atomic():
            override = DecisionOverride.objects.create(
                case=case,
                original_result=original_result,
                overridden_outcome=overridden_outcome,
                reason=reason,
                reviewer=reviewer
            )
            override.full_clean()
            override.save()
            return override

    @staticmethod
    def update_decision_override(override, version: int = None, **fields):
        """
        Update decision override fields with optimistic locking.
        
        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(override, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in DecisionOverride._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            updated_count = DecisionOverride.objects.filter(
                id=override.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DecisionOverride.objects.filter(id=override.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Decision override not found.")
                raise ValidationError(
                    f"Decision override was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DecisionOverride.objects.get(id=override.id)

    @staticmethod
    def soft_delete_decision_override(override, version: int = None, deleted_by=None) -> DecisionOverride:
        """
        Soft delete a decision override with optimistic locking.
        
        Args:
            override: DecisionOverride instance to soft delete
            version: Expected version number for optimistic locking
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted DecisionOverride instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(override, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DecisionOverride.objects.filter(
                id=override.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DecisionOverride.objects.filter(id=override.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Decision override not found.")
                raise ValidationError(
                    f"Decision override was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DecisionOverride.objects.get(id=override.id)
    
    @staticmethod
    def delete_decision_override(override, version: int = None, deleted_by=None):
        """
        Delete a decision override (soft delete).
        
        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        DecisionOverrideRepository.soft_delete_decision_override(override, version=version, deleted_by=deleted_by)
        return True
    
    @staticmethod
    def restore_decision_override(override, version: int = None, restored_by=None) -> DecisionOverride:
        """
        Restore a soft-deleted decision override with optimistic locking.
        
        Args:
            override: DecisionOverride instance to restore
            version: Expected version number for optimistic locking
            restored_by: User performing the restoration
            
        Returns:
            Restored DecisionOverride instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(override, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DecisionOverride.objects.filter(
                id=override.id,
                version=expected_version,
                is_deleted=True,
            ).update(
                is_deleted=False,
                deleted_at=None,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DecisionOverride.objects.filter(id=override.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Decision override not found.")
                raise ValidationError(
                    f"Decision override was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DecisionOverride.objects.get(id=override.id)

