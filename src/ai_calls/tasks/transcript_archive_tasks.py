"""
Celery tasks for transcript archiving (hot/cold storage).
"""
import logging
from celery import shared_task
from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector
from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository

logger = logging.getLogger('django')


@shared_task
def archive_old_transcripts_task(days_threshold: int = 90):
    """
    Background task to archive old transcripts to cold storage.
    
    Moves transcripts older than threshold from hot to cold storage.
    Runs daily via Celery Beat.
    """
    try:
        transcripts = CallTranscriptSelector.get_hot_storage_transcripts(days_threshold)
        archived_count = 0
        
        for transcript in transcripts:
            try:
                CallTranscriptRepository.archive_transcript(transcript)
                archived_count += 1
            except Exception as e:
                logger.error(f"Error archiving transcript {transcript.id}: {e}")
        
        logger.info(f"Archived {archived_count} transcripts to cold storage")
        return archived_count
        
    except Exception as e:
        logger.error(f"Error archiving transcripts: {e}")
        return 0
