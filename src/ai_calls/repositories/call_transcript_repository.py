from django.db import transaction, IntegrityError
from django.db.models import Max
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_calls.models.call_transcript import CallTranscript
import logging

logger = logging.getLogger('django')


class CallTranscriptRepository:
    """Repository for CallTranscript write operations."""

    @staticmethod
    def get_next_turn_number(call_session) -> int:
        """
        Atomically get the next turn number for a call session.
        Prevents race conditions in concurrent requests.
        """
        with transaction.atomic():
            # Use select_for_update to lock the row and prevent concurrent access
            max_turn = CallTranscript.objects.filter(
                call_session=call_session,
                is_deleted=False,
            ).select_for_update().aggregate(Max('turn_number'))['turn_number__max']
            
            return (max_turn or 0) + 1

    @staticmethod
    def create_transcript_turn(call_session, turn_number: int = None, turn_type: str = None, text: str = None, **fields):
        """
        Create a new transcript turn with atomic turn number assignment.
        
        If turn_number is not provided, it will be atomically generated.
        """
        with transaction.atomic():
            # Get turn number atomically if not provided
            if turn_number is None:
                turn_number = CallTranscriptRepository.get_next_turn_number(call_session)
            
            # Attempt to create with retry on IntegrityError (race condition)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    transcript = CallTranscript.objects.create(
                        call_session=call_session,
                        turn_number=turn_number,
                        turn_type=turn_type,
                        text=text,
                        version=1,
                        is_deleted=False,
                        **fields
                    )
                    transcript.full_clean()
                    transcript.save()
                    return transcript
                except IntegrityError as e:
                    if attempt < max_retries - 1:
                        # Turn number conflict - get next available
                        turn_number = CallTranscriptRepository.get_next_turn_number(call_session)
                        logger.warning(f"Turn number conflict for session {call_session.id}, retrying with turn {turn_number}")
                    else:
                        logger.error(f"Failed to create transcript turn after {max_retries} attempts: {e}")
                        raise

    @staticmethod
    def update_transcript_turn(transcript: CallTranscript, version: int = None, **fields):
        """
        Update transcript turn fields with optimistic locking.

        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(transcript, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in CallTranscript._meta.fields}
            protected_fields = {"id", "version", "created_at", "timestamp", "call_session", "turn_number"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = timezone.now()

            updated_count = CallTranscript.objects.filter(
                id=transcript.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CallTranscript.objects.filter(id=transcript.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Transcript turn not found.")
                raise ValidationError(
                    f"Transcript turn was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CallTranscript.objects.get(id=transcript.id)

    @staticmethod
    def archive_transcript(transcript: CallTranscript, version: int = None):
        """Move transcript to cold storage with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(transcript, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = CallTranscript.objects.filter(
                id=transcript.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                storage_tier="cold",
                archived_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CallTranscript.objects.filter(id=transcript.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Transcript turn not found.")
                raise ValidationError(
                    f"Transcript turn was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CallTranscript.objects.get(id=transcript.id)

    @staticmethod
    def soft_delete_transcript_turn(transcript: CallTranscript, version: int = None) -> CallTranscript:
        """Soft delete a transcript turn with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(transcript, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = CallTranscript.objects.filter(
                id=transcript.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CallTranscript.objects.filter(id=transcript.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Transcript turn not found.")
                raise ValidationError(
                    f"Transcript turn was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CallTranscript.objects.get(id=transcript.id)

    @staticmethod
    def delete_transcript_turn(transcript: CallTranscript, version: int = None):
        """
        Delete a transcript turn.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        return CallTranscriptRepository.soft_delete_transcript_turn(transcript, version=version)
