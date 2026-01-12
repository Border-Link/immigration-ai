import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from datetime import timedelta
from ai_calls.models.call_session import CallSession
from ai_calls.selectors.call_session_selector import CallSessionSelector
from ai_calls.services.call_session_service import CallSessionService

logger = logging.getLogger('django')

# Constants
CALL_DURATION_SECONDS = 30 * 60  # 30 minutes
WARNING_5_MIN_SECONDS = 25 * 60  # 25 minutes (5 min remaining)
WARNING_1_MIN_SECONDS = 29 * 60  # 29 minutes (1 min remaining)


class TimeboxService:
    """Service for timebox enforcement (independent background scheduler)."""

    @staticmethod
    def schedule_timebox_enforcement(session_id: str, started_at) -> Optional[str]:
        """
        Schedule background task to enforce timebox.
        
        Creates Celery task scheduled for 30 minutes from started_at.
        Task runs independently of API traffic.
        
        Returns:
        - Task ID for cancellation if needed, or None on error
        """
        try:
            from ai_calls.tasks.timebox_tasks import enforce_timebox_task
            
            # Calculate when to run (30 minutes from start)
            run_at = started_at + timedelta(seconds=CALL_DURATION_SECONDS)
            
            # Schedule task
            result = enforce_timebox_task.apply_async(
                args=[session_id],
                eta=run_at
            )
            
            logger.info(f"Scheduled timebox enforcement for session {session_id}, task_id: {result.id if result else 'N/A'}")
            return result.id if result else None
            
        except Exception as e:
            logger.error(f"Error scheduling timebox enforcement for session {session_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def cancel_timebox_enforcement(task_id: Optional[str]) -> bool:
        """Cancel scheduled timebox enforcement task."""
        if not task_id:
            return True  # No task to cancel
        
        try:
            from celery import current_app
            current_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled timebox enforcement task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling timebox enforcement task {task_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def check_time_remaining(session_id: str) -> Dict[str, Any]:
        """
        Check remaining time for call.
        
        Returns:
        - Dict with 'remaining_seconds', 'warning_level' (none/5min/1min)
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session or not call_session.started_at:
                return {'remaining_seconds': 0, 'warning_level': None}
            
            elapsed = (timezone.now() - call_session.started_at).total_seconds()
            remaining = max(0, CALL_DURATION_SECONDS - elapsed)
            
            warning_level = None
            if remaining <= 60:
                warning_level = '1min'
            elif remaining <= 300:  # 5 minutes
                warning_level = '5min'
            
            return {
                'remaining_seconds': int(remaining),
                'warning_level': warning_level
            }
        except Exception as e:
            logger.error(f"Error checking time remaining for session {session_id}: {e}")
            return {'remaining_seconds': 0, 'warning_level': None}

    @staticmethod
    def should_warn(session_id: str) -> bool:
        """Check if warning should be shown (5 min or 1 min remaining)."""
        time_info = TimeboxService.check_time_remaining(session_id)
        return time_info['warning_level'] is not None

    @staticmethod
    def should_terminate(session_id: str) -> bool:
        """Check if call should be auto-terminated (30 minutes reached)."""
        time_info = TimeboxService.check_time_remaining(session_id)
        return time_info['remaining_seconds'] <= 0

    @staticmethod
    def enforce_timebox(session_id: str) -> Optional[CallSession]:
        """
        Background task: Enforce 30-minute timebox.
        
        Called by Celery scheduler at 30-minute mark.
        Independent of API traffic - ensures timebox is enforced even if
        user stops making requests.
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.warning(f"Call session {session_id} not found for timebox enforcement")
                return None
            
            # Only enforce if still in progress
            if call_session.status != 'in_progress':
                logger.info(f"Call session {session_id} is not in_progress (status: {call_session.status}), skipping timebox enforcement")
                return None
            
            # Auto-terminate
            from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
            
            call_session = CallSessionService.end_call(session_id, reason='timebox_expired')
            
            # Log auto-termination
            if call_session:
                CallAuditLogRepository.create_audit_log(
                    call_session=call_session,
                    event_type='auto_termination',
                    description="Call auto-terminated after 30 minutes",
                    metadata={'reason': 'timebox_expired'}
                )
            
            logger.info(f"Timebox enforced for session {session_id}")
            return call_session
            
        except Exception as e:
            logger.error(f"Error enforcing timebox for session {session_id}: {e}")
            return None

    @staticmethod
    def send_warning(session_id: str, warning_level: str) -> bool:
        """
        Send timebox warning (5 min or 1 min remaining).
        
        Called by background scheduler, not dependent on user requests.
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session or call_session.status != 'in_progress':
                return False
            
            from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
            
            message = f"You have {warning_level} remaining in this call."
            if warning_level == '1min':
                message = "You have 1 minute remaining. The call will end automatically."
            
            CallAuditLogRepository.create_audit_log(
                call_session=call_session,
                event_type='timebox_warning',
                description=message,
                metadata={'warning_level': warning_level}
            )
            
            logger.info(f"Timebox warning sent for session {session_id}: {warning_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending timebox warning for session {session_id}: {e}")
            return False
