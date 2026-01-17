from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_decisions.models.eligibility_result import EligibilityResult
from immigration_cases.models.case import Case
from rules_knowledge.models.visa_type import VisaType
from rules_knowledge.models.visa_rule_version import VisaRuleVersion


class EligibilityResultRepository:
    """Repository for EligibilityResult write operations."""

    @staticmethod
    def create_eligibility_result(case: Case, visa_type: VisaType, rule_version: VisaRuleVersion,
                                 outcome: str, confidence: float = 0.0, reasoning_summary: str = None,
                                 missing_facts: dict = None):
        """Create a new eligibility result."""
        with transaction.atomic():
            result = EligibilityResult.objects.create(
                case=case,
                visa_type=visa_type,
                rule_version=rule_version,
                outcome=outcome,
                confidence=confidence,
                reasoning_summary=reasoning_summary,
                missing_facts=missing_facts,
                version=1,
                is_deleted=False,
            )
            result.full_clean()
            result.save()
            return result

    @staticmethod
    def update_eligibility_result(result: EligibilityResult, version: int = None, **fields):
        """
        Update eligibility result fields with optimistic locking.

        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(result, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed = {"outcome", "confidence", "reasoning_summary", "missing_facts"}
            update_fields = {k: v for k, v in fields.items() if k in allowed}

            update_fields["updated_at"] = timezone.now()

            updated = EligibilityResult.objects.filter(
                id=result.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated != 1:
                current_version = EligibilityResult.objects.filter(id=result.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Eligibility result not found.")
                raise ValidationError(
                    f"Eligibility result was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return EligibilityResult.objects.get(id=result.id)

    @staticmethod
    def soft_delete_eligibility_result(result: EligibilityResult, version: int = None) -> EligibilityResult:
        """Soft delete an eligibility result with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(result, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated = EligibilityResult.objects.filter(
                id=result.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated != 1:
                current_version = EligibilityResult.objects.filter(id=result.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Eligibility result not found.")
                raise ValidationError(
                    f"Eligibility result was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return EligibilityResult.objects.get(id=result.id)

    @staticmethod
    def delete_eligibility_result(result: EligibilityResult, version: int = None):
        """
        Delete an eligibility result.

        CRITICAL: deletion must be soft-delete.
        """
        return EligibilityResultRepository.soft_delete_eligibility_result(result, version=version)

