from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from immigration_cases.models.case import Case
from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator


class CaseRepository:
    """Repository for Case write operations."""

    @staticmethod
    def create_case(user, jurisdiction: str, status: str = 'draft'):
        """Create a new case."""
        with transaction.atomic():
            case = Case.objects.create(
                user=user,
                jurisdiction=jurisdiction,
                status=status,
                version=1  # Initialize version for optimistic locking
            )
            case.full_clean()
            case.save()
            return case

    @staticmethod
    def update_case(case: Case, version=None, changed_by=None, reason=None, metadata=None, **fields):
        """Update case fields with status transition validation, history tracking, and optimistic locking."""
        from immigration_cases.repositories.case_status_history_repository import CaseStatusHistoryRepository
        
        with transaction.atomic():
            # Optimistic locking check
            if version is not None:
                current_version = Case.objects.filter(id=case.id).values_list('version', flat=True).first()
                if current_version != version:
                    raise ValidationError(
                        f"Case was modified by another user. "
                        f"Expected version {version}, got {current_version}. "
                        f"Please refresh and try again."
                    )
            
            # Track status changes
            previous_status = case.status
            status_changed = False
            
            # Validate status transition if status is being updated
            if 'status' in fields:
                is_valid, error = CaseStatusTransitionValidator.validate_transition(
                    case.status,
                    fields['status']
                )
                if not is_valid:
                    raise ValidationError(error)
                
                # Validate prerequisites for status transition
                from immigration_cases.helpers.case_validator import CaseValidator
                is_valid, error = CaseValidator.validate_case_prerequisites_for_status(
                    case,
                    fields['status']
                )
                if not is_valid:
                    raise ValidationError(error)
                
                status_changed = True
            
            # Increment version for optimistic locking
            # Use F() expression to ensure atomic increment
            Case.objects.filter(id=case.id).update(version=F('version') + 1)
            
            # Refresh case to get updated version
            case.refresh_from_db()
            
            # Update fields (excluding version which is already updated)
            for key, value in fields.items():
                if hasattr(case, key) and key != 'version':
                    setattr(case, key, value)
            
            case.full_clean()
            case.save()
            
            # Create status history entry if status changed
            if status_changed:
                CaseStatusHistoryRepository.create_status_history(
                    case=case,
                    previous_status=previous_status,
                    new_status=case.status,
                    changed_by=changed_by,
                    reason=reason,
                    metadata=metadata or {}
                )
            
            return case

    @staticmethod
    def delete_case(case: Case):
        """Hard delete a case (use soft_delete_case for soft delete)."""
        with transaction.atomic():
            case.delete()
    
    @staticmethod
    def soft_delete_case(case: Case, deleted_by=None):
        """Soft delete a case."""
        with transaction.atomic():
            # IMPORTANT: avoid refresh_from_db() before persisting is_deleted/deleted_at,
            # otherwise those in-memory changes get overwritten.
            Case.objects.filter(id=case.id).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                version=F('version') + 1,
            )
            case.refresh_from_db()
            return case
    
    @staticmethod
    def restore_case(case: Case, restored_by=None):
        """Restore a soft-deleted case."""
        with transaction.atomic():
            Case.objects.filter(id=case.id).update(
                is_deleted=False,
                deleted_at=None,
                version=F('version') + 1,
            )
            case.refresh_from_db()
            return case

