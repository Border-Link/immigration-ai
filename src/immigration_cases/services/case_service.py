import logging
from typing import Optional
from helpers.cache_utils import cache_result
from immigration_cases.models.case import Case
from immigration_cases.repositories.case_repository import CaseRepository
from immigration_cases.selectors.case_selector import CaseSelector
from users_access.selectors.user_selector import UserSelector
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')


class CaseService:
    """Service for Case business logic."""

    @staticmethod
    def create_case(user_id: str, jurisdiction: str, status: str = 'draft') -> Optional[Case]:
        """Create a new case."""
        try:
            user = UserSelector.get_by_id(user_id)
            case = CaseRepository.create_case(user, jurisdiction, status)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='immigration_cases',
                    message=f"Case created for user {user_id} in jurisdiction {jurisdiction}",
                    func_name='create_case',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return case
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - case list changes frequently
    def get_all():
        """Get all cases."""
        try:
            return CaseSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all cases: {e}")
            return Case.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['user_id'])  # 5 minutes - cache cases by user
    def get_by_user(user_id: str):
        """Get cases by user."""
        try:
            user = UserSelector.get_by_id(user_id)
            return CaseSelector.get_by_user(user)
        except Exception as e:
            logger.error(f"Error fetching cases for user {user_id}: {e}")
            return Case.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['case_id'])  # 10 minutes - cache case by ID (already cached in selector, but service layer adds value)
    def get_by_id(case_id: str) -> Optional[Case]:
        """Get case by ID."""
        try:
            return CaseSelector.get_by_id(case_id)
        except Case.DoesNotExist:
            logger.warning(f"Case {case_id} not found")
            return None
        except ValueError as e:
            logger.error(f"Invalid case ID format '{case_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def update_case(case_id: str, updated_by_id: str = None, reason: str = None, version: int = None, **fields) -> Optional[Case]:
        """Update case fields with optimistic locking and status history tracking."""
        from users_access.selectors.user_selector import UserSelector
        from django.core.exceptions import ValidationError
        
        try:
            case = CaseSelector.get_by_id(case_id)
            
            updated_by = None
            if updated_by_id:
                updated_by = UserSelector.get_by_id(updated_by_id)
            
            updated_case = CaseRepository.update_case(
                case,
                version=version,
                changed_by=updated_by,
                reason=reason,
                **fields
            )
            
            # Log audit event
            try:
                changes = ', '.join([f"{k}={v}" for k, v in fields.items()])
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='immigration_cases',
                    message=f"Case {case_id} updated: {changes}",
                    func_name='update_case',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_case
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return None
        except ValidationError as e:
            logger.error(f"Validation error updating case {case_id}: {e}")
            raise e  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {e}")
            return None

    @staticmethod
    def delete_case(case_id: str, deleted_by_id: str = None, hard_delete: bool = False) -> bool:
        """Delete a case (soft delete by default, hard delete if hard_delete=True)."""
        from users_access.selectors.user_selector import UserSelector
        
        try:
            case = CaseSelector.get_by_id(case_id)
            
            deleted_by = None
            if deleted_by_id:
                deleted_by = UserSelector.get_by_id(deleted_by_id)
            
            if hard_delete:
                CaseRepository.delete_case(case)
            else:
                CaseRepository.soft_delete_case(case, deleted_by=deleted_by)
            
            # Log audit event
            try:
                delete_type = "hard deleted" if hard_delete else "soft deleted"
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='immigration_cases',
                    message=f"Case {case_id} {delete_type}",
                    func_name='delete_case',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {e}")
            return False
    
    @staticmethod
    def restore_case(case_id: str, restored_by_id: str = None) -> Optional[Case]:
        """Restore a soft-deleted case."""
        from users_access.selectors.user_selector import UserSelector
        
        try:
            # Get case including soft-deleted ones
            case = Case.objects.select_related('user', 'user__profile').get(id=case_id)
            
            if not case.is_deleted:
                logger.warning(f"Case {case_id} is not soft-deleted, no restoration needed.")
                return case
            
            restored_by = None
            if restored_by_id:
                restored_by = UserSelector.get_by_id(restored_by_id)
            
            restored_case = CaseRepository.restore_case(case, restored_by=restored_by)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='immigration_cases',
                    message=f"Case {case_id} restored",
                    func_name='restore_case',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return restored_case
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error restoring case {case_id}: {e}")
            return None

    @staticmethod
    def get_by_filters(user_id=None, jurisdiction=None, status=None, date_from=None, date_to=None, updated_date_from=None, updated_date_to=None):
        """Get cases with advanced filtering for admin."""
        try:
            return CaseSelector.get_by_filters(
                user_id=user_id,
                jurisdiction=jurisdiction,
                status=status,
                date_from=date_from,
                date_to=date_to,
                updated_date_from=updated_date_from,
                updated_date_to=updated_date_to
            )
        except Exception as e:
            logger.error(f"Error filtering cases: {e}")
            return Case.objects.none()
