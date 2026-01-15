from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_calls.models.call_session import CallSession
from ai_calls.helpers.state_machine_validator import CallSessionStateValidator


class CallSessionRepository:
    """Repository for CallSession write operations."""

    @staticmethod
    def create_call_session(case, user, **fields):
        """Create a new call session."""
        with transaction.atomic():
            call_session = CallSession.objects.create(
                case=case,
                user=user,
                status='created',
                version=1,  # Initialize version for optimistic locking
                **fields
            )
            call_session.full_clean()
            call_session.save()
            return call_session

    @staticmethod
    def update_call_session(call_session: CallSession, version=None, **fields):
        """Update call session fields with state machine validation and optimistic locking."""
        with transaction.atomic():
            # Optimistic locking check
            if version is not None:
                current_version = CallSession.objects.filter(id=call_session.id).values_list('version', flat=True).first()
                if current_version != version:
                    raise ValidationError(
                        f"Call session was modified by another user. "
                        f"Expected version {version}, got {current_version}. "
                        f"Please refresh and try again."
                    )
            
            # Validate status transition if status is being updated
            if 'status' in fields:
                is_valid, error = CallSessionStateValidator.validate_transition(
                    call_session.status,
                    fields['status']
                )
                if not is_valid:
                    raise ValidationError(error)
            
            # Increment version for optimistic locking
            CallSession.objects.filter(id=call_session.id).update(version=F('version') + 1)
            
            # Refresh to get updated version
            call_session.refresh_from_db()
            
            # Update fields (excluding version which is already updated)
            for key, value in fields.items():
                if hasattr(call_session, key) and key != 'version':
                    setattr(call_session, key, value)
            
            # Compute context hash if context_bundle is updated
            if 'context_bundle' in fields and call_session.context_bundle:
                call_session.context_hash = call_session.compute_context_hash()
            
            call_session.full_clean()
            call_session.save()
            return call_session

    @staticmethod
    def update_status(call_session: CallSession, new_status: str, version=None):
        """Update call session status with state machine validation."""
        return CallSessionRepository.update_call_session(
            call_session,
            version=version,
            status=new_status
        )

    @staticmethod
    def soft_delete_call_session(call_session: CallSession):
        """Soft delete a call session."""
        with transaction.atomic():
            call_session.is_deleted = True
            call_session.deleted_at = timezone.now()
            CallSession.objects.filter(id=call_session.id).update(version=F('version') + 1)
            call_session.refresh_from_db()
            call_session.full_clean()
            call_session.save()
            return call_session

    @staticmethod
    def delete_call_session(call_session: CallSession):
        """Hard delete a call session."""
        with transaction.atomic():
            call_session.delete()
