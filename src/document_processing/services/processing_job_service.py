"""
Service for ProcessingJob business logic.
"""
import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from document_processing.models.processing_job import ProcessingJob
from document_processing.repositories.processing_job_repository import ProcessingJobRepository
from document_processing.selectors.processing_job_selector import ProcessingJobSelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "processing_jobs"


class ProcessingJobService:
    """Service for ProcessingJob business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda job: job is not None)
    def create_processing_job(
        case_document_id: str,
        processing_type: str,
        priority: int = 5,
        max_retries: int = 3,
        celery_task_id: str = None,
        created_by_id: str = None,
        metadata: dict = None
    ):
        """
        Create a new processing job.
        
        Requires: Case must have a completed payment before processing jobs can be created.
        Note: This provides defense in depth - payment is also validated at document upload and processing task levels.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return None
            
            # Validate payment requirement (defense in depth)
            is_valid, error = PaymentValidator.validate_case_has_payment(
                case_document.case, 
                operation_name="processing job creation"
            )
            if not is_valid:
                logger.warning(f"Processing job creation blocked for case {case_document.case.id}: {error}")
                raise ValidationError(error)
            
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
    @cache_result(timeout=180, keys=[], namespace=namespace, user_scope="global")  # 3 minutes - jobs change frequently as they process
    def get_all():
        """Get all processing jobs."""
        try:
            return ProcessingJobSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all processing jobs: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['job_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache job by ID
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
    @cache_result(timeout=180, keys=['case_document_id'], namespace=namespace, user_scope="global")  # 3 minutes - jobs for document change as processing occurs
    def get_by_case_document(case_document_id: str):
        """Get processing jobs by case document."""
        try:
            return ProcessingJobSelector.get_by_case_document(case_document_id)
        except Exception as e:
            logger.error(f"Error fetching processing jobs for case document {case_document_id}: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    @cache_result(timeout=180, keys=['status'], namespace=namespace, user_scope="global")  # 3 minutes - jobs by status change frequently
    def get_by_status(status: str):
        """Get processing jobs by status."""
        try:
            return ProcessingJobSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching processing jobs by status {status}: {e}")
            return ProcessingJobSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['processing_type'], namespace=namespace, user_scope="global")  # 5 minutes - cache jobs by type
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
    @invalidate_cache(namespace, predicate=lambda job: job is not None)
    def update_processing_job(job_id: str, **fields) -> Optional[ProcessingJob]:
        """
        Update processing job.
        
        Requires: Case must have a completed payment before processing jobs can be updated.
        Note: System-initiated updates during processing may bypass this, but user-initiated updates require payment.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            job = ProcessingJobSelector.get_by_id(job_id)
            if not job:
                logger.error(f"Processing job {job_id} not found")
                return None
            
            # Validate payment requirement (for user-initiated updates)
            is_valid, error = PaymentValidator.validate_case_has_payment(
                job.case_document.case, 
                operation_name="processing job update"
            )
            if not is_valid:
                logger.warning(f"Processing job update blocked for case {job.case_document.case.id}: {error}")
                raise ValidationError(error)
            
            return ProcessingJobRepository.update_processing_job(job, **fields)
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating processing job {job_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda job: job is not None)
    def update_status(job_id: str, status: str, error_message: str = None, error_type: str = None) -> Optional[ProcessingJob]:
        """Update processing job status with optional error information."""
        try:
            job = ProcessingJobSelector.get_by_id(job_id)
            updated_job = ProcessingJobRepository.update_status(job, status)
            
            # Update error fields if provided
            if error_message or error_type:
                update_fields = {}
                if error_message:
                    update_fields['error_message'] = error_message
                if error_type:
                    update_fields['error_type'] = error_type
                if update_fields:
                    updated_job = ProcessingJobRepository.update_processing_job(updated_job, **update_fields)
            
            return updated_job
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
    @invalidate_cache(namespace, predicate=bool)
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
    @cache_result(timeout=30, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get processing job statistics."""
        try:
            return ProcessingJobSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting processing job statistics: {e}")
            return {}
    
    @staticmethod
    def update_cost_tracking(
        job_id: str,
        llm_tokens_used: int = None,
        llm_cost_usd: float = None,
        ocr_cost_usd: float = None
    ) -> Optional[ProcessingJob]:
        """Update cost tracking for a processing job."""
        try:
            from decimal import Decimal, ROUND_HALF_UP

            job = ProcessingJobSelector.get_by_id(job_id)
            if not job:
                return None
            
            update_fields = {}
            if llm_tokens_used is not None:
                update_fields['llm_tokens_used'] = llm_tokens_used
            if llm_cost_usd is not None:
                update_fields['llm_cost_usd'] = llm_cost_usd
            if ocr_cost_usd is not None:
                update_fields['ocr_cost_usd'] = ocr_cost_usd
            
            # Calculate total cost
            # Use Decimal arithmetic to avoid float precision causing validation errors
            # (model fields are DecimalField with 6 decimal places).
            total_cost = Decimal("0")
            if llm_cost_usd is not None:
                total_cost += Decimal(str(llm_cost_usd))
            if ocr_cost_usd is not None:
                total_cost += Decimal(str(ocr_cost_usd))
            if total_cost > 0:
                total_cost = total_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                update_fields['total_cost_usd'] = total_cost
            
            if update_fields:
                return ProcessingJobRepository.update_processing_job(job, **update_fields)
            
            return job
        except ProcessingJob.DoesNotExist:
            logger.error(f"Processing job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating cost tracking for job {job_id}: {e}")
            return None