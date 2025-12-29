import logging
from typing import Optional
from immigration_cases.models.case import Case
from immigration_cases.repositories.case_repository import CaseRepository
from immigration_cases.selectors.case_selector import CaseSelector
from users_access.selectors.user_selector import UserSelector

logger = logging.getLogger('django')


class CaseService:
    """Service for Case business logic."""

    @staticmethod
    def create_case(user_id: str, jurisdiction: str, status: str = 'draft') -> Optional[Case]:
        """Create a new case."""
        try:
            user = UserSelector.get_by_id(user_id)
            return CaseRepository.create_case(user, jurisdiction, status)
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all cases."""
        try:
            return CaseSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all cases: {e}")
            return Case.objects.none()

    @staticmethod
    def get_by_user(user_id: str):
        """Get cases by user."""
        try:
            user = UserSelector.get_by_id(user_id)
            return CaseSelector.get_by_user(user)
        except Exception as e:
            logger.error(f"Error fetching cases for user {user_id}: {e}")
            return Case.objects.none()

    @staticmethod
    def get_by_id(case_id: str) -> Optional[Case]:
        """Get case by ID."""
        try:
            return CaseSelector.get_by_id(case_id)
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {e}")
            return None

    @staticmethod
    def update_case(case_id: str, **fields) -> Optional[Case]:
        """Update case fields."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return CaseRepository.update_case(case, **fields)
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {e}")
            return None

    @staticmethod
    def delete_case(case_id: str) -> bool:
        """Delete a case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            CaseRepository.delete_case(case)
            return True
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {e}")
            return False

