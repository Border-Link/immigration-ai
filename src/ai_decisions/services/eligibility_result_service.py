import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result
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
        """
        Create a new eligibility result.
        
        Requires: Case must have a completed payment before eligibility results can be created.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found when creating eligibility result")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="eligibility result creation")
            if not is_valid:
                logger.warning(f"Eligibility result creation blocked for case {case_id}: {error}")
                raise ValidationError(error)
            
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
        """
        Update eligibility result fields.
        
        Requires: Case must have a completed payment before eligibility results can be updated.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            result = EligibilityResultSelector.get_by_id(result_id)
            if not result:
                logger.error(f"Eligibility result {result_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(result.case, operation_name="eligibility result update")
            if not is_valid:
                logger.warning(f"Eligibility result update blocked for case {result.case.id}: {error}")
                raise ValidationError(error)
            
            return EligibilityResultRepository.update_eligibility_result(result, **fields)
        except EligibilityResult.DoesNotExist:
            logger.error(f"Eligibility result {result_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating eligibility result {result_id}: {e}")
            return None

    @staticmethod
    def delete_eligibility_result(result_id: str) -> bool:
        """
        Delete an eligibility result.
        
        Requires: Case must have a completed payment before eligibility results can be deleted.
        This prevents abuse and ensures only paid cases can manage their eligibility results.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            result = EligibilityResultSelector.get_by_id(result_id)
            if not result:
                logger.error(f"Eligibility result {result_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(result.case, operation_name="eligibility result deletion")
            if not is_valid:
                logger.warning(f"Eligibility result deletion blocked for case {result.case.id}: {error}")
                raise ValidationError(error)
            
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
    def get_by_user_access(user):
        """
        Get eligibility results filtered by user access.
        
        Regular users can only see results for their own cases.
        Admin/reviewer/superuser can see all results.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet of eligibility results
        """
        try:
            all_results = EligibilityResultService.get_all()
            
            # If user is admin/reviewer/superuser, return all results
            if user.is_superuser or user.is_staff or user.role in ['admin', 'reviewer']:
                return all_results
            
            # Regular users can only see their own cases' results
            return all_results.filter(case__user=user)
        except Exception as e:
            logger.error(f"Error fetching eligibility results by user access: {e}")
            return EligibilityResultSelector.get_none()
    
    @staticmethod
    def get_by_case_with_access_check(case_id: str, user):
        """
        Get eligibility results for a case, verifying user has access to the case.
        
        Args:
            case_id: Case ID
            user: User instance
            
        Returns:
            Tuple of (results QuerySet, error_message)
            If error_message is not None, user doesn't have access or case not found.
        """
        from immigration_cases.services.case_service import CaseService
        
        try:
            case = CaseService.get_by_id(case_id)
            if not case:
                return None, f"Case with ID '{case_id}' not found."
            
            # Check user access
            from main_system.permissions.case_ownership import CaseOwnershipPermission
            if not CaseOwnershipPermission.has_case_access(user, case):
                return None, "You do not have permission to access this case."
            
            return EligibilityResultService.get_by_case(case_id), None
        except Exception as e:
            logger.error(f"Error fetching eligibility results for case {case_id}: {e}")
            return None, f"Error fetching eligibility results: {str(e)}"
    
    @staticmethod
    def get_statistics():
        """Get eligibility result statistics."""
        try:
            return EligibilityResultSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting eligibility result statistics: {e}")
            return {}
