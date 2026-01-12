import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from django.core.exceptions import ValidationError
from main_system.utils.cache_utils import cache_result
from ai_calls.models.call_session import CallSession
from ai_calls.repositories.call_session_repository import CallSessionRepository
from ai_calls.selectors.call_session_selector import CallSessionSelector
from immigration_cases.selectors.case_selector import CaseSelector
from users_access.selectors.user_selector import UserSelector

logger = logging.getLogger('django')


class CallSessionService:
    """Service for CallSession business logic."""

    @staticmethod
    def create_call_session(case_id: str, user_id: str, parent_session_id: Optional[str] = None) -> Optional[CallSession]:
        """
        Create a new call session.
        
        Validates:
        - Case exists and belongs to user
        - Case is in valid state (not closed)
        - User doesn't have active call for this case
        - If retry: Previous call ended abruptly (within 10 minutes)
        - Case has sufficient context (facts, documents, etc.)
        
        Args:
            case_id: Case ID
            user_id: User ID
            parent_session_id: Optional parent session ID if this is a retry
        """
        MAX_ABRUPT_END_DURATION_SECONDS = 10 * 60  # 10 minutes
        
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.warning(f"Case {case_id} not found")
                return None
            
            user = UserSelector.get_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return None
            
            # Validate case belongs to user
            if case.user_id != user_id:
                logger.warning(f"Case {case_id} does not belong to user {user_id}")
                return None
            
            # Validate case is not closed
            if case.status == 'closed':
                logger.warning(f"Cannot create call for closed case {case_id}")
                return None
            
            # Check for active call
            active_call = CallSessionSelector.get_active_call_for_case(case)
            if active_call:
                logger.warning(f"Case {case_id} already has active call {active_call.id}")
                return None
            
            # Validate retry conditions if this is a retry
            parent_session = None
            retry_count = 0
            if parent_session_id:
                # This is a retry - check parent session
                parent_session = CallSessionSelector.get_by_id(parent_session_id)
                if not parent_session or parent_session.case_id != case_id:
                    logger.warning(f"Invalid parent session {parent_session_id} for case {case_id}")
                    return None
                
                # Check if parent session ended abruptly (within 10 minutes)
                if parent_session.status not in ['terminated', 'failed', 'expired']:
                    logger.warning(f"Parent session {parent_session_id} did not end abruptly (status: {parent_session.status}). Retries only allowed for abruptly ended calls.")
                    return None
                
                # Check if call duration was less than 10 minutes
                if parent_session.duration_seconds is not None:
                    if parent_session.duration_seconds >= MAX_ABRUPT_END_DURATION_SECONDS:
                        logger.warning(
                            f"Parent session {parent_session_id} lasted {parent_session.duration_seconds}s "
                            f"(>= {MAX_ABRUPT_END_DURATION_SECONDS}s). Retries only allowed for calls that ended within 10 minutes."
                        )
                        return None
                elif parent_session.started_at:
                    # Calculate duration if not set
                    if parent_session.ended_at:
                        duration = (parent_session.ended_at - parent_session.started_at).total_seconds()
                        if duration >= MAX_ABRUPT_END_DURATION_SECONDS:
                            logger.warning(
                                f"Parent session {parent_session_id} lasted {duration}s "
                                f"(>= {MAX_ABRUPT_END_DURATION_SECONDS}s). Retries only allowed for calls that ended within 10 minutes."
                            )
                            return None
                
                # Count retries (for tracking purposes)
                retry_count = parent_session.retry_count + 1
            
            # Create call session
            call_session = CallSessionRepository.create_call_session(
                case=case,
                user=user,
                status='created',
                parent_session=parent_session,
                retry_count=retry_count
            )
            
            logger.info(f"Call session {call_session.id} created for case {case_id} (retry_count: {retry_count}, is_retry: {parent_session_id is not None})")
            return call_session
            
        except Exception as e:
            logger.error(f"Error creating call session: {e}", exc_info=True)
            return None

    @staticmethod
    def prepare_call_session(session_id: str) -> Optional[CallSession]:
        """
        Prepare call session by building context bundle.
        
        Steps:
        1. Validate current status is 'created' (state machine enforcement)
        2. Build case context (CaseContextBuilder)
        3. Compute context hash (SHA-256)
        4. Seal context bundle (mark as read-only)
        5. Validate transition 'created' → 'ready'
        6. Update status to 'ready' with optimistic locking
        """
        try:
            from ai_calls.services.case_context_builder import CaseContextBuilder
            
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.warning(f"Call session {session_id} not found")
                return None
            
            # Validate current status
            if call_session.status != 'created':
                logger.warning(f"Call session {session_id} is not in 'created' status (current: {call_session.status})")
                return None
            
            # Build context bundle
            context_bundle = CaseContextBuilder.build_context_bundle(str(call_session.case.id))
            if not context_bundle:
                logger.error(f"Failed to build context bundle for case {call_session.case.id}")
                # Mark session as failed
                try:
                    CallSessionRepository.update_call_session(
                        call_session,
                        status='failed'
                    )
                except Exception:
                    pass
                return None
            
            # Validate context bundle has minimum required fields
            is_valid, error_message = CaseContextBuilder.validate_context_bundle(context_bundle)
            if not is_valid:
                logger.error(f"Context bundle validation failed for case {call_session.case.id}: {error_message}")
                try:
                    CallSessionRepository.update_call_session(
                        call_session,
                        version=call_session.version,
                        status='failed'
                    )
                except Exception:
                    pass
                return None
            
            # Compute context hash
            context_hash = CaseContextBuilder.compute_context_hash(context_bundle)
            
            # Update call session with version check
            call_session = CallSessionRepository.update_call_session(
                call_session,
                version=call_session.version,  # Pass current version for optimistic locking
                context_bundle=context_bundle,
                context_hash=context_hash,
                context_version=call_session.context_version + 1,  # Increment version
                ready_at=timezone.now(),
                status='ready'
            )
            
            logger.info(f"Call session {session_id} prepared and ready")
            return call_session
            
        except ValidationError as e:
            logger.error(f"Validation error preparing call session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error preparing call session {session_id}: {e}")
            return None

    @staticmethod
    def start_call(session_id: str) -> Optional[CallSession]:
        """
        Start the call.
        
        Steps:
        1. Validate session is 'ready' (state machine check)
        2. Validate transition 'ready' → 'in_progress'
        3. Initialize WebRTC session (placeholder for now)
        4. Schedule timebox enforcement task (background scheduler)
        5. Update status to 'in_progress' with optimistic locking
        6. Record started_at timestamp
        """
        try:
            from ai_calls.services.timebox_service import TimeboxService
            
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.warning(f"Call session {session_id} not found")
                return None
            
            # Validate current status
            if call_session.status != 'ready':
                logger.warning(f"Call session {session_id} is not in 'ready' status (current: {call_session.status})")
                return None
            
            # Validate context bundle exists
            if not call_session.context_bundle:
                logger.error(f"Call session {session_id} has no context bundle")
                # Mark as failed
                try:
                    CallSessionRepository.update_call_session(
                        call_session,
                        version=call_session.version,
                        status='failed'
                    )
                except Exception:
                    pass
                return None
            
            # Schedule timebox enforcement
            task_id = TimeboxService.schedule_timebox_enforcement(session_id, timezone.now())
            
            # Update call session with version check, storing task_id
            call_session = CallSessionRepository.update_call_session(
                call_session,
                version=call_session.version,  # Pass current version for optimistic locking
                status='in_progress',
                started_at=timezone.now(),
                webrtc_session_id=f"webrtc_{session_id}",  # Placeholder
                timebox_task_id=task_id  # Store task_id for proper cancellation
            )
            
            logger.info(f"Call session {session_id} started")
            return call_session
            
        except ValidationError as e:
            logger.error(f"Validation error starting call session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error starting call session {session_id}: {e}")
            return None

    @staticmethod
    def end_call(session_id: str, reason: str = 'completed') -> Optional[CallSession]:
        """
        End the call normally.
        
        Steps:
        1. Validate session is 'in_progress' (state machine check)
        2. Validate transition 'in_progress' → 'completed'
        3. Cancel timebox enforcement task
        4. Generate post-call summary
        5. Attach summary to case timeline
        6. Update status to 'completed' with optimistic locking
        7. Record ended_at and duration_seconds
        """
        try:
            from ai_calls.services.timebox_service import TimeboxService
            from ai_calls.services.post_call_summary_service import PostCallSummaryService
            
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.warning(f"Call session {session_id} not found")
                return None
            
            # Validate current status
            if call_session.status != 'in_progress':
                logger.warning(f"Call session {session_id} is not in 'in_progress' status (current: {call_session.status})")
                return None
            
            # Cancel timebox enforcement using stored task_id
            if call_session.timebox_task_id:
                TimeboxService.cancel_timebox_enforcement(call_session.timebox_task_id)
                logger.info(f"Cancelled timebox enforcement task {call_session.timebox_task_id} for session {session_id}")
            
            # Calculate duration
            if call_session.started_at:
                duration_seconds = int((timezone.now() - call_session.started_at).total_seconds())
            else:
                duration_seconds = 0
            
            # Update call session with version check, clearing task_id
            call_session = CallSessionRepository.update_call_session(
                call_session,
                version=call_session.version,  # Pass current version for optimistic locking
                status='completed',
                ended_at=timezone.now(),
                duration_seconds=duration_seconds,
                timebox_task_id=None  # Clear task_id since task is cancelled
            )
            
            # Generate post-call summary
            summary = PostCallSummaryService.generate_summary(session_id)
            if summary:
                call_session = CallSessionRepository.update_call_session(
                    call_session,
                    summary=summary
                )
                # Attach to case timeline
                PostCallSummaryService.attach_to_case_timeline(summary.id, call_session.case_id)
            
            logger.info(f"Call session {session_id} ended normally")
            return call_session
            
        except ValidationError as e:
            logger.error(f"Validation error ending call session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error ending call session {session_id}: {e}")
            return None

    @staticmethod
    def terminate_call(session_id: str, reason: str, terminated_by_user_id: str) -> Optional[CallSession]:
        """
        Manually terminate call (user or admin).
        
        Steps:
        1. Stop timebox timer
        2. Generate partial summary (if call had content)
        3. Update status to 'terminated'
        4. Log termination in audit log
        """
        try:
            from ai_calls.services.timebox_service import TimeboxService
            from ai_calls.services.post_call_summary_service import PostCallSummaryService
            from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
            
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.warning(f"Call session {session_id} not found")
                return None
            
            # Cancel timebox enforcement using stored task_id
            if call_session.timebox_task_id:
                TimeboxService.cancel_timebox_enforcement(call_session.timebox_task_id)
                logger.info(f"Cancelled timebox enforcement task {call_session.timebox_task_id} for session {session_id}")
            
            # Calculate duration
            if call_session.started_at:
                duration_seconds = int((timezone.now() - call_session.started_at).total_seconds())
            else:
                duration_seconds = 0
            
            # Update call session with version check, clearing task_id
            call_session = CallSessionRepository.update_call_session(
                call_session,
                version=call_session.version,  # Pass current version for optimistic locking
                status='terminated',
                ended_at=timezone.now(),
                duration_seconds=duration_seconds,
                timebox_task_id=None  # Clear task_id since task is cancelled
            )
            
            # Generate partial summary if call had content
            from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector
            transcripts = CallTranscriptSelector.get_by_call_session(call_session)
            if transcripts.exists():
                summary = PostCallSummaryService.generate_summary(session_id)
                if summary:
                    call_session = CallSessionRepository.update_call_session(
                        call_session,
                        summary=summary
                    )
            
            # Log termination
            CallAuditLogRepository.create_audit_log(
                call_session=call_session,
                event_type='manual_termination',
                description=f"Call terminated by user {terminated_by_user_id}: {reason}",
                metadata={'reason': reason, 'terminated_by': terminated_by_user_id}
            )
            
            logger.info(f"Call session {session_id} terminated: {reason}")
            return call_session
            
        except ValidationError as e:
            logger.error(f"Validation error terminating call session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error terminating call session {session_id}: {e}")
            return None

    @staticmethod
    def fail_call_session(session_id: str, reason: str, error_details: Optional[Dict] = None) -> Optional[CallSession]:
        """
        Mark call session as failed due to system error.
        
        Args:
            session_id: Call session ID
            reason: Reason for failure
            error_details: Optional error details dict
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.warning(f"Call session {session_id} not found for failure marking")
                return None
            
            # Only allow failure from non-terminal states
            if call_session.status in ['completed', 'expired', 'terminated']:
                logger.warning(f"Cannot mark terminal session {session_id} as failed")
                return None
            
            # Cancel timebox enforcement if task_id exists
            if call_session.timebox_task_id:
                from ai_calls.services.timebox_service import TimeboxService
                TimeboxService.cancel_timebox_enforcement(call_session.timebox_task_id)
                logger.info(f"Cancelled timebox enforcement task {call_session.timebox_task_id} for failed session {session_id}")
            
            # Calculate duration if started
            duration_seconds = None
            if call_session.started_at:
                duration_seconds = int((timezone.now() - call_session.started_at).total_seconds())
            
            # Update to failed status, clearing task_id
            call_session = CallSessionRepository.update_call_session(
                call_session,
                version=call_session.version,
                status='failed',
                ended_at=timezone.now() if call_session.started_at else None,
                duration_seconds=duration_seconds,
                timebox_task_id=None  # Clear task_id since task is cancelled
            )
            
            # Log failure in audit log
            from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
            CallAuditLogRepository.create_audit_log(
                call_session=call_session,
                event_type='system_error',
                description=f"Call session failed: {reason}",
                metadata={'reason': reason, 'error_details': error_details}
            )
            
            logger.error(f"Call session {session_id} marked as failed: {reason}")
            return call_session
            
        except Exception as e:
            logger.error(f"Error marking call session {session_id} as failed: {e}", exc_info=True)
            return None

    @staticmethod
    def update_heartbeat(session_id: str) -> Optional[CallSession]:
        """
        Update heartbeat timestamp for active call session.
        Used to track client liveness.
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                return None
            
            # Only update heartbeat for in_progress sessions
            if call_session.status != 'in_progress':
                return call_session
            
            # Update heartbeat (no version check needed for heartbeat)
            from django.db.models import F
            from django.db import transaction
            
            with transaction.atomic():
                CallSession.objects.filter(id=call_session.id).update(
                    last_heartbeat_at=timezone.now()
                )
                call_session.refresh_from_db()
            
            return call_session
            
        except Exception as e:
            logger.error(f"Error updating heartbeat for session {session_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=['session_id'])
    def get_call_session(session_id: str) -> Optional[CallSession]:
        """Get call session by ID."""
        try:
            return CallSessionSelector.get_by_id(session_id)
        except CallSession.DoesNotExist:
            logger.warning(f"Call session {session_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching call session {session_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])
    def get_active_call_for_case(case_id: str) -> Optional[CallSession]:
        """Get active call session for a case (if exists)."""
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                return None
            return CallSessionSelector.get_active_call_for_case(case)
        except Exception as e:
            logger.error(f"Error fetching active call for case {case_id}: {e}")
            return None
