from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
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
                missing_facts=missing_facts
            )
            result.full_clean()
            result.save()
            return result

    @staticmethod
    def update_eligibility_result(result: EligibilityResult, **fields):
        """Update eligibility result fields."""
        return BaseRepositoryMixin.update_model_fields(
            result,
            **fields,
            cache_keys=[f'eligibility_result:{result.id}']
        )

    @staticmethod
    def delete_eligibility_result(result: EligibilityResult):
        """Delete an eligibility result."""
        with transaction.atomic():
            result.delete()

