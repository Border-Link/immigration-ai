import logging
from typing import Optional

from django.core.exceptions import ValidationError

from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository
from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector

logger = logging.getLogger("django")


class TranscriptArchiveService:
    """
    Service for transcript archiving (hot/cold storage).

    Tasks/controllers should call this service (not repositories directly).
    """

    @staticmethod
    def archive_old_transcripts(days_threshold: int = 90) -> int:
        """
        Archive old transcripts to cold storage.

        Returns number of successfully archived transcript turns.
        """
        transcripts = CallTranscriptSelector.get_hot_storage_transcripts(days_threshold)
        archived_count = 0

        for transcript in transcripts:
            try:
                # Pass current version for conflict detection.
                CallTranscriptRepository.archive_transcript(transcript, version=getattr(transcript, "version", None))
                archived_count += 1
            except ValidationError as e:
                # Concurrency-safe: another worker may have updated/archived it already.
                logger.warning(f"Transcript archive conflict for transcript {transcript.id}: {e}")
            except Exception as e:
                logger.error(f"Error archiving transcript {transcript.id}: {e}")

        return archived_count

