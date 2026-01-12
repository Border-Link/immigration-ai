"""
Celery tasks for timebox enforcement.
"""
import logging
from celery import shared_task
from ai_calls.services.timebox_service import TimeboxService

logger = logging.getLogger('django')


@shared_task(bind=True, max_retries=3)
def enforce_timebox_task(self, session_id: str):
    """
    Background task to enforce 30-minute timebox.
    
    This task runs independently of API traffic to ensure timebox
    is enforced even if user stops making requests.
    """
    try:
        result = TimeboxService.enforce_timebox(session_id)
        if result:
            logger.info(f"Timebox enforced for session {session_id}")
        else:
            logger.warning(f"Timebox enforcement failed for session {session_id}")
        return result
    except Exception as e:
        logger.error(f"Error enforcing timebox for session {session_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_timebox_warning_task(session_id: str, warning_level: str):
    """
    Background task to send timebox warning.
    
    Sends warning at 5 minutes and 1 minute remaining.
    """
    try:
        TimeboxService.send_warning(session_id, warning_level)
        logger.info(f"Timebox warning sent for session {session_id}: {warning_level}")
    except Exception as e:
        logger.error(f"Error sending timebox warning for session {session_id}: {e}")
