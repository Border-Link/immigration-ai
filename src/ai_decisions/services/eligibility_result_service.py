import logging
from typing import Optional
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
    def get_all():
        """Get all eligibility results."""
        try:
            return EligibilityResultSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all eligibility results: {e}")
            return EligibilityResult.objects.none()

    @staticmethod
    def get_by_case(case_id: str):
        """Get eligibility results by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return EligibilityResultSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching eligibility results for case {case_id}: {e}")
            return EligibilityResult.objects.none()

    @staticmethod
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

