from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_calls.models.call_session import CallSession
from ai_calls.helpers.state_machine_validator import CallSessionStateValidator
from ai_calls.helpers.context_hashing import compute_context_hash
from main_system.utils.cache_utils import bump_namespace


class CallSessionRepository:
    """Repository for CallSession write operations."""
    CACHE_NAMESPACE = "call_sessions"

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
            # Defensive: invalidate call session caches even if signals are bypassed elsewhere.
            bump_namespace(CallSessionRepository.CACHE_NAMESPACE)
            return call_session

    @staticmethod
    def update_call_session(call_session: CallSession, version=None, **fields):
        """
        Update call session fields with state machine validation and optimistic locking.

        IMPORTANT:
        - This uses a single conditional UPDATE (WHERE id AND version) to prevent
          last-write-wins overwrites under concurrency.
        - It bumps the call_sessions cache namespace because QuerySet.update() bypasses signals.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(call_session, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")
            
            # Validate status transition if status is being updated
            if 'status' in fields:
                is_valid, error = CallSessionStateValidator.validate_transition(
                    call_session.status,
                    fields['status']
                )
                if not is_valid:
                    raise ValidationError(error)

            # Compute context hash if context_bundle is updated (unless explicitly provided)
            if 'context_bundle' in fields and fields.get('context_bundle') and 'context_hash' not in fields:
                fields['context_hash'] = compute_context_hash(fields.get('context_bundle'))

            # Only allow updating known concrete fields; never allow changing PK / version directly.
            allowed_fields = {f.name for f in CallSession._meta.fields}
            protected_fields = {'id', 'version', 'created_at'}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if 'updated_at' in allowed_fields:
                update_fields['updated_at'] = timezone.now()

            qs = CallSession.objects.filter(
                id=call_session.id,
                version=expected_version,
                is_deleted=False,
            )
            updated_count = qs.update(
                **update_fields,
                version=F('version') + 1,
            )

            if updated_count != 1:
                current_version = CallSession.objects.filter(id=call_session.id).values_list('version', flat=True).first()
                if current_version is None:
                    raise ValidationError("Call session not found.")
                raise ValidationError(
                    f"Call session was modified by another user. "
                    f"Expected version {expected_version}, got {current_version}. "
                    f"Please refresh and try again."
                )

            bump_namespace(CallSessionRepository.CACHE_NAMESPACE)
            return CallSession.objects.get(id=call_session.id)

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
            expected_version = getattr(call_session, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = CallSession.objects.filter(
                id=call_session.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F('version') + 1,
            )

            if updated_count != 1:
                current_version = CallSession.objects.filter(id=call_session.id).values_list('version', flat=True).first()
                if current_version is None:
                    raise ValidationError("Call session not found.")
                raise ValidationError(
                    f"Call session was modified by another user. "
                    f"Expected version {expected_version}, got {current_version}. "
                    f"Please refresh and try again."
                )

            bump_namespace(CallSessionRepository.CACHE_NAMESPACE)
            return CallSession.objects.get(id=call_session.id)

    @staticmethod
    def delete_call_session(call_session: CallSession):
        """
        Delete a call session.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        return CallSessionRepository.soft_delete_call_session(call_session)

    @staticmethod
    def update_heartbeat(call_session: CallSession):
        """
        Update heartbeat timestamp for an active call session.
        Note: This is intentionally a lightweight write (no optimistic-lock requirement).
        """
        with transaction.atomic():
            CallSession.objects.filter(id=call_session.id).update(last_heartbeat_at=timezone.now())
            call_session.refresh_from_db()
            return call_session
