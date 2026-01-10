"""
Service for ProcessingJob business logic.
"""
import logging
from typing import Optional
from document_processing.models.processing_job import ProcessingJob
from document_processing.repositories.processing_job_repository import ProcessingJobRepository
from document_processing.selectors.processing_job_selector import ProcessingJobSelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector

logger = logging.getLogger('django')


class ProcessingJobService:
    """Service for ProcessingJob business logic."""

    @staticmethod
    def create_processing_job(
        case_document_id: str,
        processing_type: str,
        priority: int = 5,
        max_retries: int = 3,
        celery_task_id: str = None,
        created_by_id: str = None,
        metadata: dict = None
    ):
        """Create a new processing job."""
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return None
            
            created_by = None
            if created_by_id:
                from users_access.selectors.user_selector import UserSelector
                created_by = UserSelector.get_by_id(created_by_id)
            
            return ProcessingJobRepository.create_processing_job(
                case_document=case_document,
                processing_type=processing_type,
                priority=priority,
                max_retries=max_retries,
                celery_task_id=celery_task_id,
                created_by=created_by,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error creating processing job: {e}", exc_info=True)
            return None

    @staticmethod
    def get_all():
        """Get all processing jobs."""
        try:
            return ProcessingJobSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all processing jobs: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def get_by_id(job_id: str) -> Optional[ProcessingJob]:
        """Get processing job by ID."""
        try:
            return ProcessingJobSelector.get_by_id(job_id)
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching processing job {job_id}: {e}")
            return None

    @staticmethod
    def get_by_case_document(case_document_id: str):
        """Get processing jobs by case document."""
        try:
            return ProcessingJobSelector.get_by_case_document(case_document_id)
        except Exception as e:
            logger.error(f"Error fetching processing jobs for case document {case_document_id}: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def get_by_status(status: str):
        """Get processing jobs by status."""
        try:
            return ProcessingJobSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching processing jobs by status {status}: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def get_by_processing_type(processing_type: str):
        """Get processing jobs by processing type."""
        try:
            return ProcessingJobSelector.get_by_processing_type(processing_type)
        except Exception as e:
            logger.error(f"Error fetching processing jobs by type {processing_type}: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def get_by_celery_task_id(celery_task_id: str) -> Optional[ProcessingJob]:
        """Get processing job by Celery task ID."""
        try:
            return ProcessingJobSelector.get_by_celery_task_id(celery_task_id)
        except Exception as e:
            logger.error(f"Error fetching processing job by task ID {celery_task_id}: {e}")
            return None

    @staticmethod
    def get_pending():
        """Get all pending processing jobs."""
        try:
            return ProcessingJobSelector.get_pending()
        except Exception as e:
            logger.error(f"Error fetching pending processing jobs: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def get_failed():
        """Get all failed processing jobs."""
        try:
            return ProcessingJobSelector.get_failed()
        except Exception as e:
            logger.error(f"Error fetching failed processing jobs: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def update_processing_job(job_id: str, **fields) -> Optional[ProcessingJob]:
        """Update processing job."""
        try:
            job = ProcessingJobSelector.get_by_id(job_id)
            return ProcessingJobRepository.update_processing_job(job, **fields)
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating processing job {job_id}: {e}")
            return None

    @staticmethod
    def update_status(job_id: str, status: str) -> Optional[ProcessingJob]:
        """Update processing job status."""
        try:
            job = ProcessingJobSelector.get_by_id(job_id)
            return ProcessingJobRepository.update_status(job, status)
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating processing job status {job_id}: {e}")
            return None

    @staticmethod
    def increment_retry_count(job_id: str) -> Optional[ProcessingJob]:
        """Increment retry count for a processing job."""
        try:
            job = ProcessingJobSelector.get_by_id(job_id)
            return ProcessingJobRepository.increment_retry_count(job)
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error incrementing retry count for job {job_id}: {e}")
            return None

    @staticmethod
    def delete_processing_job(job_id: str) -> bool:
        """Delete processing job."""
        try:
            job = ProcessingJobSelector.get_by_id(job_id)
            ProcessingJobRepository.delete_processing_job(job)
            return True
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting processing job {job_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(
        case_document_id: str = None,
        status: str = None,
        processing_type: str = None,
        error_type: str = None,
        created_by_id: str = None,
        date_from=None,
        date_to=None,
        min_priority: int = None,
        max_retries_exceeded: bool = None
    ):
        """Get processing jobs with filters."""
        try:
            return ProcessingJobSelector.get_by_filters(
                case_document_id=case_document_id,
                status=status,
                processing_type=processing_type,
                error_type=error_type,
                created_by_id=created_by_id,
                date_from=date_from,
                date_to=date_to,
                min_priority=min_priority,
                max_retries_exceeded=max_retries_exceeded
            )
        except Exception as e:
            logger.error(f"Error fetching filtered processing jobs: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get processing job statistics."""
        try:
            return ProcessingJobSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting processing job statistics: {e}")
            return {}
