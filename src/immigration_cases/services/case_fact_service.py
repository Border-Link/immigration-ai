import logging
from typing import Optional
from helpers.cache_utils import cache_result
from immigration_cases.models.case_fact import CaseFact
from immigration_cases.repositories.case_fact_repository import CaseFactRepository
from immigration_cases.selectors.case_fact_selector import CaseFactSelector
from immigration_cases.selectors.case_selector import CaseSelector
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')


class CaseFactService:
    """Service for CaseFact business logic."""

    @staticmethod
    def create_case_fact(case_id: str, fact_key: str, fact_value, source: str = 'user') -> Optional[CaseFact]:
        """Create a new case fact."""
        from django.core.exceptions import ValidationError
        
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found when creating case fact")
                return None
            
            return CaseFactRepository.create_case_fact(case, fact_key, fact_value, source)
        except ValidationError as e:
            logger.error(f"Validation error creating case fact for case {case_id}: {e}")
            raise e  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Error creating case fact for case {case_id}: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - facts list changes frequently
    def get_all():
        """Get all case facts."""
        try:
            return CaseFactSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all case facts: {e}")
            return CaseFact.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])  # 5 minutes - cache facts by case
    def get_by_case(case_id: str):
        """Get facts by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return CaseFactSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching facts for case {case_id}: {e}")
            return CaseFact.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['fact_id'])  # 10 minutes - cache fact by ID
    def get_by_id(fact_id: str) -> Optional[CaseFact]:
        """Get case fact by ID."""
        try:
            return CaseFactSelector.get_by_id(fact_id)
        except CaseFact.DoesNotExist:
            logger.error(f"Case fact {fact_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching case fact {fact_id}: {e}")
            return None

    @staticmethod
    def update_case_fact(fact_id: str, **fields) -> Optional[CaseFact]:
        """Update case fact fields."""
        try:
            fact = CaseFactSelector.get_by_id(fact_id)
            return CaseFactRepository.update_case_fact(fact, **fields)
        except CaseFact.DoesNotExist:
            logger.error(f"Case fact {fact_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating case fact {fact_id}: {e}")
            return None

    @staticmethod
    def delete_case_fact(fact_id: str) -> bool:
        """Delete a case fact."""
        try:
            fact = CaseFactSelector.get_by_id(fact_id)
            CaseFactRepository.delete_case_fact(fact)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='immigration_cases',
                    message=f"Case fact {fact_id} deleted for case {fact.case.id}",
                    func_name='delete_case_fact',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except CaseFact.DoesNotExist:
            logger.error(f"Case fact {fact_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting case fact {fact_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(case_id=None, fact_key=None, source=None, date_from=None, date_to=None):
        """Get case facts with advanced filtering for admin."""
        try:
            return CaseFactSelector.get_by_filters(
                case_id=case_id,
                fact_key=fact_key,
                source=source,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering case facts: {e}")
            return CaseFact.objects.none()
