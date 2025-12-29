from ai_decisions.models.eligibility_result import EligibilityResult
from immigration_cases.models.case import Case
from rules_knowledge.models.visa_type import VisaType


class EligibilityResultSelector:
    """Selector for EligibilityResult read operations."""

    @staticmethod
    def get_all():
        """Get all eligibility results."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get eligibility results by case."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_visa_type(visa_type: VisaType):
        """Get eligibility results by visa type."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).filter(visa_type=visa_type).order_by('-created_at')

    @staticmethod
    def get_by_id(result_id):
        """Get eligibility result by ID."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).get(id=result_id)

