from django.db import transaction, IntegrityError
from django.db.models import Max
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
                call_session=call_session
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
    def update_transcript_turn(transcript: CallTranscript, **fields):
        """Update transcript turn fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(transcript, key):
                    setattr(transcript, key, value)
            
            transcript.full_clean()
            transcript.save()
            return transcript

    @staticmethod
    def archive_transcript(transcript: CallTranscript):
        """Move transcript to cold storage."""
        from django.utils import timezone
        
        with transaction.atomic():
            transcript.storage_tier = 'cold'
            transcript.archived_at = timezone.now()
            transcript.full_clean()
            transcript.save()
            return transcript

    @staticmethod
    def delete_transcript_turn(transcript: CallTranscript):
        """Delete a transcript turn."""
        with transaction.atomic():
            transcript.delete()
