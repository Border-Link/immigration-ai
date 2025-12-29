from human_reviews.models.decision_override import DecisionOverride
from immigration_cases.models.case import Case
from ai_decisions.models.eligibility_result import EligibilityResult
from django.conf import settings


class DecisionOverrideSelector:
    """Selector for DecisionOverride read operations."""

    @staticmethod
    def get_all():
        """Get all decision overrides."""
        return DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get overrides by case."""
        return DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_original_result(original_result: EligibilityResult):
        """Get overrides by original eligibility result."""
        return DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).filter(original_result=original_result).order_by('-created_at')

    @staticmethod
    def get_latest_by_original_result(original_result: EligibilityResult):
        """Get latest override for an eligibility result."""
        return DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).filter(original_result=original_result).order_by('-created_at').first()

    @staticmethod
    def get_by_reviewer(reviewer):
        """Get overrides by reviewer."""
        return DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).filter(reviewer=reviewer).order_by('-created_at')

    @staticmethod
    def get_by_id(override_id):
        """Get decision override by ID."""
        return DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).get(id=override_id)

