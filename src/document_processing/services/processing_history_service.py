"""
Service for ProcessingHistory business logic.
"""
import logging
from typing import Optional
from helpers.cache_utils import cache_result
from document_processing.models.processing_history import ProcessingHistory
from document_processing.repositories.processing_history_repository import ProcessingHistoryRepository
from document_processing.selectors.processing_history_selector import ProcessingHistorySelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector

logger = logging.getLogger('django')


class ProcessingHistoryService:
    """Service for ProcessingHistory business logic."""

    @staticmethod
    def create_history_entry(
        case_document_id: str,
        action: str,
        status: str,
        message: str = None,
        processing_job_id: str = None,
        user_id: str = None,
        metadata: dict = None,
        error_type: str = None,
        error_message: str = None,
        processing_time_ms: int = None
    ):
        """Create a new processing history entry."""
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return None
            
            processing_job = None
            if processing_job_id:
                from document_processing.selectors.processing_job_selector import ProcessingJobSelector
                processing_job = ProcessingJobSelector.get_by_id(processing_job_id)
            
            user = None
            if user_id:
                from users_access.selectors.user_selector import UserSelector
                user = UserSelector.get_by_id(user_id)
            
            return ProcessingHistoryRepository.create_history_entry(
                case_document=case_document,
                processing_job=processing_job,
                action=action,
                user=user,
                status=status,
                message=message,
                metadata=metadata,
                error_type=error_type,
                error_message=error_message,
                processing_time_ms=processing_time_ms
            )
        except Exception as e:
            logger.error(f"Error creating processing history entry: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=180, keys=[])  # 3 minutes - history changes frequently as processing occurs
    def get_all():
        """Get all processing history entries."""
        try:
            return ProcessingHistorySelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all processing history: {e}")
            return ProcessingHistorySelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['history_id'])  # 10 minutes - cache history entry by ID
    def get_by_id(history_id: str) -> Optional[ProcessingHistory]:
        """Get processing history entry by ID."""
        try:
            return ProcessingHistorySelector.get_by_id(history_id)
        except ProcessingHistory.DoesNotExist:
            logger.error(f"Processing history {history_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching processing history {history_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=180, keys=['case_document_id'])  # 3 minutes - history for document changes as processing occurs
    def get_by_case_document(case_document_id: str):
        """Get processing history by case document."""
        try:
            return ProcessingHistorySelector.get_by_case_document(case_document_id)
        except Exception as e:
            logger.error(f"Error fetching processing history for case document {case_document_id}: {e}")
            return ProcessingHistorySelector.get_none()

    @staticmethod
    @cache_result(timeout=180, keys=['processing_job_id'])  # 3 minutes - history for job changes as processing occurs
    def get_by_processing_job(processing_job_id: str):
        """Get processing history by processing job."""
        try:
            return ProcessingHistorySelector.get_by_processing_job(processing_job_id)
        except Exception as e:
            logger.error(f"Error fetching processing history for job {processing_job_id}: {e}")
            return ProcessingHistorySelector.get_none()

    @staticmethod
    def get_by_action(action: str):
        """Get processing history by action."""
        try:
            return ProcessingHistorySelector.get_by_action(action)
        except Exception as e:
            logger.error(f"Error fetching processing history by action {action}: {e}")
            return ProcessingHistorySelector.get_none()

    @staticmethod
    def get_by_status(status: str):
        """Get processing history by status."""
        try:
            return ProcessingHistorySelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching processing history by status {status}: {e}")
            return ProcessingHistorySelector.get_none()

    @staticmethod
    def delete_history_entry(history_id: str) -> bool:
        """Delete processing history entry."""
        try:
            history = ProcessingHistorySelector.get_by_id(history_id)
            ProcessingHistoryRepository.delete_history_entry(history)
            return True
        except ProcessingHistory.DoesNotExist:
            logger.error(f"Processing history {history_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting processing history {history_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(
        case_document_id: str = None,
        processing_job_id: str = None,
        action: str = None,
        status: str = None,
        error_type: str = None,
        user_id: str = None,
        date_from=None,
        date_to=None,
        limit: int = None
    ):
        """Get processing history with filters."""
        try:
            return ProcessingHistorySelector.get_by_filters(
                case_document_id=case_document_id,
                processing_job_id=processing_job_id,
                action=action,
                status=status,
                error_type=error_type,
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error fetching filtered processing history: {e}")
            return ProcessingHistorySelector.get_none()

    @staticmethod
    def get_statistics():
        """Get processing history statistics."""
        try:
            return ProcessingHistorySelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting processing history statistics: {e}")
            return {}
