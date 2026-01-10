"""
Repository for ProcessingJob write operations.
"""
from django.db import transaction
from django.utils import timezone
from document_processing.models.processing_job import ProcessingJob
from document_handling.models.case_document import CaseDocument


class ProcessingJobRepository:
    """Repository for ProcessingJob write operations."""

    @staticmethod
    def create_processing_job(
        case_document: CaseDocument,
        processing_type: str,
        priority: int = 5,
        max_retries: int = 3,
        celery_task_id: str = None,
        created_by=None,
        metadata: dict = None
    ):
        """Create a new processing job."""
        with transaction.atomic():
            job = ProcessingJob.objects.create(
                case_document=case_document,
                processing_type=processing_type,
                priority=priority,
                max_retries=max_retries,
                celery_task_id=celery_task_id,
                created_by=created_by,
                metadata=metadata
            )
            job.full_clean()
            job.save()
            return job

    @staticmethod
    def update_processing_job(job, **fields):
        """Update processing job fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            # Auto-update timestamps based on status
            if 'status' in fields:
                if fields['status'] == 'processing' and not job.started_at:
                    job.started_at = timezone.now()
                elif fields['status'] in ['completed', 'failed', 'cancelled'] and not job.completed_at:
                    job.completed_at = timezone.now()
            
            job.full_clean()
            job.save()
            return job

    @staticmethod
    def update_status(job, status: str):
        """Update processing job status."""
        with transaction.atomic():
            job.status = status
            if status == 'processing' and not job.started_at:
                job.started_at = timezone.now()
            elif status in ['completed', 'failed', 'cancelled'] and not job.completed_at:
                job.completed_at = timezone.now()
            job.full_clean()
            job.save()
            return job

    @staticmethod
    def increment_retry_count(job):
        """Increment retry count for a processing job."""
        with transaction.atomic():
            job.retry_count += 1
            job.full_clean()
            job.save()
            return job

    @staticmethod
    def delete_processing_job(job):
        """Delete a processing job."""
        with transaction.atomic():
            job.delete()
            return True
