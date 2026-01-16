from __future__ import annotations

import logging
import time
from typing import Optional, Tuple
from django.core.exceptions import ObjectDoesNotExist
from main_system.utils.cache_utils import cache_result, invalidate_cache
from immigration_cases.repositories.case_repository import CaseRepository
from immigration_cases.selectors.case_selector import CaseSelector
from users_access.selectors.user_selector import UserSelector
from compliance.services.audit_log_service import AuditLogService
from immigration_cases.helpers.metrics import (
    track_case_creation,
    track_case_update,
    track_case_status_transition,
    track_case_version_conflict,
    track_case_status_history,
)

logger = logging.getLogger('django')


def namespace(*args, **kwargs) -> str:
    """
    Single namespace for Case-related cached reads.
    Any write operation must bump this namespace to avoid stale reads.
    """
    return "cases"


class CaseService:
    """Service for Case business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda case: case is not None)
    def create_case(user_id: str, jurisdiction: str, status: str = 'draft') -> Optional[Case]:
        """
        Create a new case.

        Payment is required BEFORE case creation:
        - user must have a completed payment not yet attached to any case
        - on successful creation, the payment is attached to the created case
        """
        try:
            from payments.helpers.payment_validator import PaymentValidator
            from payments.selectors.payment_selector import PaymentSelector
            from payments.services.payment_service import PaymentService
            
            can_create, error = PaymentValidator.can_create_case_for_user(user_id)
            if not can_create:
                logger.warning(f"Case creation blocked for user {user_id}: {error}")
                return None
            
            user = UserSelector.get_by_id(user_id)
            case = CaseRepository.create_case(user, jurisdiction, status)

            # Attach the most recent unassigned completed payment to this case
            unassigned = PaymentSelector.get_unassigned_completed_by_user(user)
            payment = unassigned.first()
            if payment:
                PaymentService.update_payment(
                    payment_id=str(payment.id),
                    changed_by=user,
                    reason="Attached payment to newly created case",
                    case=case,
                )
            
            # Track metrics
            track_case_creation(jurisdiction=jurisdiction, status=status)
            
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
    @cache_result(timeout=300, keys=[], namespace=namespace)  # 5 minutes - case list changes frequently
    def get_all():
        """Get all cases."""
        try:
            return CaseSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all cases: {e}")
            return CaseSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['user_id'], namespace=namespace)  # 5 minutes - cache cases by user
    def get_by_user(user_id: str):
        """Get cases by user."""
        try:
            user = UserSelector.get_by_id(user_id)
            return CaseSelector.get_by_user(user)
        except Exception as e:
            logger.error(f"Error fetching cases for user {user_id}: {e}")
            return CaseSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['case_id'], namespace=namespace)  # 10 minutes - cache case by ID
    def get_by_id(case_id: str) -> Optional[Case]:
        """Get case by ID."""
        try:
            return CaseSelector.get_by_id(case_id)
        except ObjectDoesNotExist:
            logger.warning(f"Case {case_id} not found")
            return None
        except ValueError as e:
            logger.error(f"Invalid case ID format '{case_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {e}", exc_info=True)
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda result: bool(result and result[0] is not None and result[1] is None))
    def update_case(case_id: str, updated_by_id: str = None, reason: str = None, version: int = None, **fields) -> Tuple[Optional[Case], Optional[str], Optional[int]]:
        """
        Update case fields with optimistic locking and status history tracking.
        
        Returns:
            Tuple of (case, error_message, http_status_code)
            - case: Updated case if successful, None otherwise
            - error_message: Error message if failed, None if successful
            - http_status_code: HTTP status code (409 for conflicts, 404 for not found, None for success)
        """
        from users_access.selectors.user_selector import UserSelector
        from django.core.exceptions import ValidationError
        
        transition_start = None
        
        try:
            from payments.helpers.payment_validator import PaymentValidator
            
            case = CaseSelector.get_by_id(case_id)
            if not case:
                return None, f"Case with ID '{case_id}' not found.", 404
            
            # Track status transition if status is being updated
            previous_status = case.status
            new_status = fields.get('status', previous_status)
            
            # Validate payment requirement for status transitions beyond 'draft'
            # Payment is required before case can be moved to 'evaluated' or beyond
            if 'status' in fields and new_status != previous_status:
                transition_start = time.time()
                
                # Require payment for status transitions to 'evaluated' or beyond
                statuses_requiring_payment = ['evaluated', 'awaiting_review', 'reviewed']
                if new_status in statuses_requiring_payment:
                    is_valid, error = PaymentValidator.validate_case_has_payment(
                        case, 
                        operation_name=f"case status update to '{new_status}'"
                    )
                    if not is_valid:
                        logger.warning(f"Case status update blocked for case {case_id}: {error}")
                        return None, error, 400
            
            # Validate payment requirement for general case updates (jurisdiction, etc.)
            # Payment is required for any case modifications to ensure data integrity
            # Note: This is in addition to status update validation above
            if fields and 'status' not in fields:
                # General update (not status change) - require payment
                is_valid, error = PaymentValidator.validate_case_has_payment(
                    case,
                    operation_name="case update"
                )
                if not is_valid:
                    logger.warning(f"Case update blocked for case {case_id}: {error}")
                    return None, error, 400
            
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
            
            # Track metrics
            operation = 'status_change' if 'status' in fields else 'general_update'
            track_case_update(operation=operation)
            
            # Track status transition if status changed
            if transition_start and 'status' in fields:
                transition_duration = time.time() - transition_start
                track_case_status_transition(
                    from_status=previous_status,
                    to_status=fields['status'],
                    duration=transition_duration
                )
                track_case_status_history(to_status=fields['status'])
            
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
            
            return updated_case, None, None
        except ObjectDoesNotExist:
            logger.error(f"Case {case_id} not found")
            return None, f"Case with ID '{case_id}' not found.", 404
        except ValidationError as e:
            # Check if it's a version conflict
            if 'version' in str(e).lower() or 'modified by another user' in str(e):
                track_case_version_conflict(operation='update')
                return None, str(e), 409  # Conflict for optimistic locking
            logger.error(f"Validation error updating case {case_id}: {e}")
            return None, str(e), 400  # Bad request for other validation errors
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {e}", exc_info=True)
            return None, f"Error updating case: {str(e)}", 500

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_case(case_id: str, deleted_by_id: str = None, hard_delete: bool = False) -> bool:
        """
        Delete a case (soft delete by default, hard delete if hard_delete=True).
        
        Requires: Case must have a completed payment before it can be deleted.
        This prevents abuse and ensures only paid cases can be deleted.
        Note: For unpaid cases, users should contact support for deletion.
        """
        from users_access.selectors.user_selector import UserSelector
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="case deletion")
            if not is_valid:
                logger.warning(f"Case deletion blocked for case {case_id}: {error}")
                raise ValidationError(error)
            
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
        except ObjectDoesNotExist:
            logger.error(f"Case {case_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {e}")
            return False
    
    @staticmethod
    @invalidate_cache(namespace, predicate=lambda case: case is not None)
    def restore_case(case_id: str, restored_by_id: str = None) -> Optional[Case]:
        """
        Restore a soft-deleted case.
        
        Requires: Case must have a completed payment before it can be restored.
        This ensures only paid cases can be restored.
        """
        from users_access.selectors.user_selector import UserSelector
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            # Get case including soft-deleted ones
            case = CaseSelector.get_any_by_id(case_id)
            
            if not case.is_deleted:
                logger.warning(f"Case {case_id} is not soft-deleted, no restoration needed.")
                return case
            
            # Validate payment requirement (check before restoring)
            # Note: We validate payment even for soft-deleted cases to ensure they had payment before deletion
            is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="case restoration")
            if not is_valid:
                logger.warning(f"Case restoration blocked for case {case_id}: {error}")
                raise ValidationError(error)
            
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
        except ObjectDoesNotExist:
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
            logger.error(f"Error filtering cases: {e}", exc_info=True)
            return CaseSelector.get_none()
