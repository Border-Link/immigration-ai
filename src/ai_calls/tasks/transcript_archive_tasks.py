"""
Celery tasks for transcript archiving (hot/cold storage).
"""
import logging
from celery import shared_task
from ai_calls.services.transcript_archive_service import TranscriptArchiveService

logger = logging.getLogger('django')


@shared_task
def archive_old_transcripts_task(days_threshold: int = 90):
    """
    Background task to archive old transcripts to cold storage.
    
    Moves transcripts older than threshold from hot to cold storage.
    Runs daily via Celery Beat.
    """
    try:
        archived_count = TranscriptArchiveService.archive_old_transcripts(days_threshold)
        logger.info(f"Archived {archived_count} transcripts to cold storage")
        return archived_count
    except Exception as e:
        logger.error(f"Error archiving transcripts: {e}")
        return 0
