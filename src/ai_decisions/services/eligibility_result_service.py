import logging
from typing import Optional
from helpers.cache_utils import cache_result
from ai_decisions.models.eligibility_result import EligibilityResult
from ai_decisions.repositories.eligibility_result_repository import EligibilityResultRepository
from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
from immigration_cases.selectors.case_selector import CaseSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector

logger = logging.getLogger('django')


class EligibilityResultService:
    """Service for EligibilityResult business logic."""

    @staticmethod
    def create_eligibility_result(case_id: str, visa_type_id: str, rule_version_id: str,
                                 outcome: str, confidence: float = 0.0, reasoning_summary: str = None,
                                 missing_facts: dict = None) -> Optional[EligibilityResult]:
        """Create a new eligibility result."""
        try:
            case = CaseSelector.get_by_id(case_id)
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            
            return EligibilityResultRepository.create_eligibility_result(
                case=case,
                visa_type=visa_type,
                rule_version=rule_version,
                outcome=outcome,
                confidence=confidence,
                reasoning_summary=reasoning_summary,
                missing_facts=missing_facts
            )
        except Exception as e:
            logger.error(f"Error creating eligibility result: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - eligibility results change frequently
    def get_all():
        """Get all eligibility results."""
        try:
            return EligibilityResultSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all eligibility results: {e}")
            return EligibilityResultSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])  # 5 minutes - cache results by case
    def get_by_case(case_id: str):
        """Get eligibility results by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return EligibilityResultSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching eligibility results for case {case_id}: {e}")
            return EligibilityResultSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['result_id'])  # 10 minutes - cache result by ID
    def get_by_id(result_id: str) -> Optional[EligibilityResult]:
        """Get eligibility result by ID."""
        try:
            return EligibilityResultSelector.get_by_id(result_id)
        except EligibilityResult.DoesNotExist:
            logger.error(f"Eligibility result {result_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching eligibility result {result_id}: {e}")
            return None

    @staticmethod
    def update_eligibility_result(result_id: str, **fields) -> Optional[EligibilityResult]:
        """Update eligibility result fields."""
        try:
            result = EligibilityResultSelector.get_by_id(result_id)
            return EligibilityResultRepository.update_eligibility_result(result, **fields)
        except EligibilityResult.DoesNotExist:
            logger.error(f"Eligibility result {result_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating eligibility result {result_id}: {e}")
            return None

    @staticmethod
    def delete_eligibility_result(result_id: str) -> bool:
        """Delete an eligibility result."""
        try:
            result = EligibilityResultSelector.get_by_id(result_id)
            EligibilityResultRepository.delete_eligibility_result(result)
            return True
        except EligibilityResult.DoesNotExist:
            logger.error(f"Eligibility result {result_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting eligibility result {result_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(case_id: str = None, visa_type_id: str = None, outcome: str = None, 
                       min_confidence: float = None, date_from=None, date_to=None):
        """Get eligibility results with filters."""
        try:
            if case_id:
                results = EligibilityResultService.get_by_case(case_id)
            else:
                results = EligibilityResultSelector.get_all()
            
            # Apply additional filters
            if visa_type_id:
                results = results.filter(visa_type_id=visa_type_id)
            if outcome:
                results = results.filter(outcome=outcome)
            if min_confidence is not None:
                results = results.filter(confidence__gte=min_confidence)
            if date_from:
                results = results.filter(created_at__gte=date_from)
            if date_to:
                results = results.filter(created_at__lte=date_to)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching filtered eligibility results: {e}")
            return EligibilityResultSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get eligibility result statistics."""
        try:
            return EligibilityResultSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting eligibility result statistics: {e}")
            return {}
