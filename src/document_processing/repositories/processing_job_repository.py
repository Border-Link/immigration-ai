"""
Repository for ProcessingJob write operations.
"""
import time
from django.db import transaction
from django.db.models import F
from django.db.utils import OperationalError
from django.utils import timezone
from django.core.exceptions import ValidationError
from document_processing.models.processing_job import ProcessingJob
from document_handling.models.case_document import CaseDocument
from document_processing.helpers.status_transition_validator import StatusTransitionValidator


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
    def update_processing_job(job, version: int = None, **fields):
        """
        Update processing job fields with status transition validation and optimistic locking.
        
        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        # Validate status transition if status is being updated
        if 'status' in fields:
            is_valid, error = StatusTransitionValidator.validate_transition(
                job.status,
                fields['status']
            )
            if not is_valid:
                raise ValidationError(error)
        
        expected_version = version if version is not None else getattr(job, "version", None)
        if expected_version is None:
            raise ValidationError("Missing version for optimistic locking.")

        allowed_fields = {f.name for f in ProcessingJob._meta.fields}
        protected_fields = {"id", "version", "created_at"}
        update_fields = {
            k: v for k, v in fields.items()
            if k in allowed_fields and k not in protected_fields
        }

        # Auto-update timestamps based on status
        if 'status' in fields:
            if fields['status'] == 'processing' and not job.started_at:
                update_fields['started_at'] = timezone.now()
            elif fields['status'] in ['completed', 'failed', 'cancelled'] and not job.completed_at:
                update_fields['completed_at'] = timezone.now()

        # QuerySet.update bypasses auto_now; set updated_at explicitly.
        if "updated_at" in allowed_fields:
            update_fields["updated_at"] = timezone.now()

        max_attempts = 20
        base_sleep_s = 0.02
        max_sleep_s = 0.2
        last_exc: Exception | None = None

        for attempt in range(max_attempts):
            try:
                with transaction.atomic():
                    updated_count = ProcessingJob.objects.filter(
                        id=job.id,
                        version=expected_version,
                        is_deleted=False,
                    ).update(
                        **update_fields,
                        version=F("version") + 1,
                    )

                if updated_count == 1:
                    return ProcessingJob.objects.get(id=job.id)

                current_version = ProcessingJob.objects.filter(id=job.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Processing job not found.")
                raise ValidationError(
                    f"Processing job was modified by another user. Expected version {expected_version}, got {current_version}."
                )
            except OperationalError as e:
                last_exc = e
                msg = str(e).lower()
                if ("database table is locked" in msg or "database is locked" in msg) and attempt < (max_attempts - 1):
                    time.sleep(min(base_sleep_s * (2**attempt), max_sleep_s))
                    continue
                raise

        if last_exc:
            raise last_exc
        raise ValidationError("Failed to update processing job due to repeated database lock contention.")

    @staticmethod
    def update_status(job, status: str, version: int = None):
        """Update processing job status with transition validation and optimistic locking."""
        return ProcessingJobRepository.update_processing_job(
            job,
            version=version,
            status=status
        )

    @staticmethod
    def increment_retry_count(job):
        """Increment retry count for a processing job."""
        with transaction.atomic():
            job.retry_count += 1
            job.full_clean()
            job.save()
            return job

    @staticmethod
    def soft_delete_processing_job(job, version: int = None, deleted_by=None) -> ProcessingJob:
        """
        Soft delete a processing job with optimistic locking.
        
        Args:
            job: ProcessingJob instance to soft delete
            version: Expected version number for optimistic locking
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted ProcessingJob instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(job, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ProcessingJob.objects.filter(
                id=job.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ProcessingJob.objects.filter(id=job.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Processing job not found.")
                raise ValidationError(
                    f"Processing job was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ProcessingJob.objects.get(id=job.id)
    
    @staticmethod
    def delete_processing_job(job, version: int = None, deleted_by=None):
        """
        Delete a processing job (soft delete).
        
        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        ProcessingJobRepository.soft_delete_processing_job(job, version=version, deleted_by=deleted_by)
        return True
    
    @staticmethod
    def restore_processing_job(job, version: int = None, restored_by=None) -> ProcessingJob:
        """
        Restore a soft-deleted processing job with optimistic locking.
        
        Args:
            job: ProcessingJob instance to restore
            version: Expected version number for optimistic locking
            restored_by: User performing the restoration
            
        Returns:
            Restored ProcessingJob instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(job, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ProcessingJob.objects.filter(
                id=job.id,
                version=expected_version,
                is_deleted=True,
            ).update(
                is_deleted=False,
                deleted_at=None,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ProcessingJob.objects.filter(id=job.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Processing job not found.")
                raise ValidationError(
                    f"Processing job was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ProcessingJob.objects.get(id=job.id)
