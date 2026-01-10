"""
Processing Job Timeout Service

Detects and handles stuck/timeout processing jobs.
"""
import logging
from typing import List, Dict
from datetime import timedelta
from django.utils import timezone
from document_processing.models.processing_job import ProcessingJob
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.services.processing_history_service import ProcessingHistoryService

logger = logging.getLogger('django')


class ProcessingJobTimeoutService:
    """Service for detecting and handling processing job timeouts."""
    
    DEFAULT_TIMEOUT_MINUTES = 60  # 1 hour default timeout
    
    @staticmethod
    def detect_stuck_jobs(timeout_minutes: int = None) -> List[ProcessingJob]:
        """
        Detect processing jobs that have been running too long.
        
        Args:
            timeout_minutes: Timeout in minutes (uses default if None)
            
        Returns:
            List of stuck ProcessingJob instances
        """
        if timeout_minutes is None:
            timeout_minutes = ProcessingJobTimeoutService.DEFAULT_TIMEOUT_MINUTES
        
        try:
            cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
            
            stuck_jobs = ProcessingJob.objects.filter(
                status='processing',
                started_at__isnull=False,
                started_at__lt=cutoff
            )
            
            return list(stuck_jobs)
            
        except Exception as e:
            logger.error(f"Error detecting stuck jobs: {e}", exc_info=True)
            return []
    
    @staticmethod
    def cancel_stuck_job(job_id: str, reason: str = "Job timeout") -> bool:
        """
        Cancel a stuck processing job.
        
        Args:
            job_id: UUID of the processing job
            reason: Reason for cancellation
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            job = ProcessingJobService.get_by_id(job_id)
            if not job:
                logger.error(f"Processing job {job_id} not found")
                return False
            
            if job.status != 'processing':
                logger.warning(f"Job {job_id} is not in 'processing' status, cannot cancel")
                return False
            
            # Update status to failed
            updated_job = ProcessingJobService.update_status(
                str(job.id),
                'failed',
                error_message=reason,
                error_type='timeout'
            )
            
            if not updated_job:
                return False
            
            # Set completed_at
            ProcessingJobService.update_processing_job(
                str(updated_job.id),
                completed_at=timezone.now()
            )
            
            # Log timeout
            ProcessingHistoryService.create_history_entry(
                case_document_id=str(updated_job.case_document.id),
                processing_job_id=str(updated_job.id),
                action='job_failed',
                status='failure',
                message=reason,
                error_type='timeout',
                metadata={
                    'timeout_minutes': ProcessingJobTimeoutService.DEFAULT_TIMEOUT_MINUTES,
                    'started_at': updated_job.started_at.isoformat() if updated_job.started_at else None
                }
            )
            
            logger.info(f"Cancelled stuck job {job_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling stuck job {job_id}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def cleanup_stuck_jobs(timeout_minutes: int = None) -> Dict[str, int]:
        """
        Cancel all stuck processing jobs.
        
        Args:
            timeout_minutes: Timeout in minutes (uses default if None)
            
        Returns:
            Dict with cleanup statistics:
            {
                'cancelled': int,
                'failed': int
            }
        """
        stats = {
            'cancelled': 0,
            'failed': 0
        }
        
        try:
            stuck_jobs = ProcessingJobTimeoutService.detect_stuck_jobs(timeout_minutes)
            
            for job in stuck_jobs:
                processing_time = timezone.now() - job.started_at if job.started_at else timedelta(0)
                reason = f"Job timeout after {processing_time.total_seconds() / 60:.1f} minutes"
                
                if ProcessingJobTimeoutService.cancel_stuck_job(str(job.id), reason):
                    stats['cancelled'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Cleanup stuck jobs completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in cleanup stuck jobs: {e}", exc_info=True)
            return stats
