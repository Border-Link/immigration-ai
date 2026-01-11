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

    @staticmethod
    def get_by_filters(case_id=None, reviewer_id=None, original_result_id=None, overridden_outcome=None, date_from=None, date_to=None):
        """Get decision overrides with advanced filtering for admin."""
        queryset = DecisionOverride.objects.select_related(
            'case',
            'case__user',
            'original_result',
            'original_result__visa_type',
            'reviewer',
            'reviewer__profile'
        ).all()
        
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        
        if original_result_id:
            queryset = queryset.filter(original_result_id=original_result_id)
        
        if overridden_outcome:
            queryset = queryset.filter(overridden_outcome=overridden_outcome)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
