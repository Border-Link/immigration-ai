from django.db import transaction
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
    def update_decision_override(override, **fields):
        """Update decision override fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(override, key):
                    setattr(override, key, value)
            override.full_clean()
            override.save()
            return override

    @staticmethod
    def delete_decision_override(override):
        """Delete a decision override."""
        with transaction.atomic():
            override.delete()

