"""
Processing Job Retry Service

Handles automatic retry logic for failed processing jobs.
"""
import logging
from typing import Optional, Dict
from django.utils import timezone
from document_processing.models.processing_job import ProcessingJob
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.services.processing_history_service import ProcessingHistoryService
from document_handling.tasks.document_tasks import process_document_task

logger = logging.getLogger('django')


class ProcessingJobRetryService:
    """Service for handling processing job retries."""
    
    @staticmethod
    def should_retry(job: ProcessingJob) -> bool:
        """
        Check if a job should be retried.
        
        Args:
            job: ProcessingJob instance
            
        Returns:
            True if job should be retried, False otherwise
        """
        if job.status != 'failed':
            return False
        
        if job.retry_count >= job.max_retries:
            logger.info(f"Job {job.id} has exceeded max retries ({job.max_retries})")
            return False
        
        return True
    
    @staticmethod
    def retry_job(job_id: str) -> Optional[ProcessingJob]:
        """
        Retry a failed processing job.
        
        Requires: Case must have a completed payment before processing jobs can be retried.
        
        Args:
            job_id: UUID of the processing job
            
        Returns:
            Updated ProcessingJob instance or None if retry failed
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            job = ProcessingJobService.get_by_id(job_id)
            if not job:
                logger.error(f"Processing job {job_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(
                job.case_document.case, 
                operation_name="processing job retry"
            )
            if not is_valid:
                logger.warning(f"Processing job retry blocked for case {job.case_document.case.id}: {error}")
                raise ValidationError(error)
            
            if not ProcessingJobRetryService.should_retry(job):
                logger.warning(f"Job {job_id} should not be retried")
                return None
            
            # Increment retry count
            updated_job = ProcessingJobService.increment_retry_count(job_id)
            if not updated_job:
                logger.error(f"Failed to increment retry count for job {job_id}")
                return None
            
            # Reset status to pending
            updated_job = ProcessingJobService.update_status(str(updated_job.id), 'pending')
            if not updated_job:
                logger.error(f"Failed to update status for job {job_id}")
                return None
            
            # Clear error fields
            updated_job = ProcessingJobService.update_processing_job(
                str(updated_job.id),
                error_message=None,
                error_type=None
            )
            
            # Log retry attempt
            ProcessingHistoryService.create_history_entry(
                case_document_id=str(updated_job.case_document.id),
                processing_job_id=str(updated_job.id),
                action='retry_attempted',
                status='success',
                message=f"Retry attempt {updated_job.retry_count} of {updated_job.max_retries}",
                metadata={'retry_count': updated_job.retry_count}
            )
            
            # Queue new Celery task
            try:
                process_document_task.delay(str(updated_job.case_document.id))
                logger.info(f"Retry queued for job {job_id}, retry count: {updated_job.retry_count}")
            except Exception as e:
                logger.error(f"Failed to queue retry task for job {job_id}: {e}", exc_info=True)
                # Update status back to failed
                ProcessingJobService.update_status(
                    str(updated_job.id),
                    'failed',
                    error_message=f"Failed to queue retry: {str(e)}",
                    error_type='retry_queue_failed'
                )
                return None
            
            return updated_job
            
        except Exception as e:
            logger.error(f"Error retrying job {job_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def auto_retry_failed_jobs(max_retries: int = None) -> Dict[str, int]:
        """
        Automatically retry all failed jobs that haven't exceeded max retries.
        
        Args:
            max_retries: Optional override for max retries (uses job's max_retries if None)
            
        Returns:
            Dict with retry statistics:
            {
                'retried': int,
                'skipped': int,
                'failed': int
            }
        """
        stats = {
            'retried': 0,
            'skipped': 0,
            'failed': 0
        }
        
        try:
            failed_jobs = ProcessingJobService.get_failed()
            
            for job in failed_jobs:
                if ProcessingJobRetryService.should_retry(job):
                    result = ProcessingJobRetryService.retry_job(str(job.id))
                    if result:
                        stats['retried'] += 1
                    else:
                        stats['failed'] += 1
                else:
                    stats['skipped'] += 1
            
            logger.info(f"Auto-retry completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in auto-retry: {e}", exc_info=True)
            return stats
