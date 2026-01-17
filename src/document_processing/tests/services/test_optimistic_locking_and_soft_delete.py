"""
Tests for optimistic locking, race conditions, conflict detection, and soft delete
in document_processing module.
"""

import pytest
from django.core.exceptions import ValidationError
from threading import Thread, Barrier
from document_processing.models.processing_job import ProcessingJob
from document_processing.models.processing_history import ProcessingHistory
from document_processing.repositories.processing_job_repository import ProcessingJobRepository
from document_processing.repositories.processing_history_repository import ProcessingHistoryRepository
from document_processing.selectors.processing_job_selector import ProcessingJobSelector
from document_processing.selectors.processing_history_selector import ProcessingHistorySelector
from document_processing.services.processing_job_service import ProcessingJobService


@pytest.mark.django_db(transaction=True)
class TestProcessingJobOptimisticLocking:
    """Tests for optimistic locking in ProcessingJob."""

    def test_create_processing_job_has_version_one(self, processing_job_service, case_document):
        """New jobs should start with version 1."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        assert job.version == 1
        assert job.is_deleted is False
        assert job.deleted_at is None

    def test_update_processing_job_increments_version(self, processing_job_service, case_document):
        """Updating a job should increment its version."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        initial_version = job.version
        
        updated = ProcessingJobRepository.update_processing_job(
            job,
            version=initial_version,
            status="queued"
        )
        
        assert updated.version == initial_version + 1
        assert updated.status == "queued"

    def test_update_processing_job_version_conflict_raises_error(self, processing_job_service, case_document):
        """Updating with wrong version should raise ValidationError."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        initial_version = job.version
        
        # First update succeeds
        ProcessingJobRepository.update_processing_job(
            job,
            version=initial_version,
            status="queued"
        )
        
        # Second update with stale version should fail
        with pytest.raises(ValidationError) as exc_info:
            ProcessingJobRepository.update_processing_job(
                job,
                version=initial_version,  # Stale version
                status="failed"
            )
        
        assert "modified by another user" in str(exc_info.value).lower()

    def test_concurrent_updates_race_condition(self, processing_job_service, case_document):
        """Test that concurrent updates are handled correctly."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        initial_version = job.version
        results = []
        errors = []
        barrier = Barrier(2)
        
        def update_job(thread_id):
            try:
                barrier.wait()  # Synchronize threads
                updated = ProcessingJobRepository.update_processing_job(
                    job,
                    version=initial_version,
                    status="queued" if thread_id == 1 else "failed"
                )
                results.append((thread_id, updated.version))
            except ValidationError as e:
                errors.append((thread_id, str(e)))
        
        # Start two threads trying to update simultaneously
        thread1 = Thread(target=update_job, args=(1,))
        thread2 = Thread(target=update_job, args=(2,))
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # One should succeed, one should fail with version conflict
        assert len(results) == 1, "Exactly one update should succeed"
        assert len(errors) == 1, "Exactly one update should fail"
        assert "modified by another user" in errors[0][1].lower()


@pytest.mark.django_db
class TestProcessingJobSoftDelete:
    """Tests for soft delete in ProcessingJob."""

    def test_soft_delete_processing_job(self, processing_job_service, case_document):
        """Soft deleting a job should mark it as deleted."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        initial_version = job.version
        
        deleted = ProcessingJobRepository.soft_delete_processing_job(
            job,
            version=initial_version
        )
        
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None
        assert deleted.version == initial_version + 1

    def test_soft_delete_filters_from_selector(self, processing_job_service, case_document):
        """Soft-deleted jobs should not appear in selectors."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        
        # Job should be visible before deletion
        found = ProcessingJobSelector.get_by_id(str(job.id))
        assert found is not None
        
        # Soft delete
        ProcessingJobRepository.soft_delete_processing_job(
            job,
            version=job.version
        )
        
        # Job should not be visible after deletion
        with pytest.raises(ProcessingJob.DoesNotExist):
            ProcessingJobSelector.get_by_id(str(job.id))

    def test_service_delete_uses_soft_delete(self, processing_job_service, case_document):
        """Service delete method should use soft delete."""
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=5
        )
        initial_version = job.version
        
        result = processing_job_service.delete_processing_job(
            str(job.id),
            version=initial_version
        )
        
        assert result is True
        
        # Job should be soft-deleted
        from document_processing.models.processing_job import ProcessingJob
        deleted_job = ProcessingJob.objects.get(id=job.id)
        assert deleted_job.is_deleted is True
        
        # Should not appear in selector
        with pytest.raises(ProcessingJob.DoesNotExist):
            ProcessingJobSelector.get_by_id(str(job.id))


@pytest.mark.django_db
class TestProcessingHistorySoftDelete:
    """Tests for soft delete in ProcessingHistory."""

    def test_soft_delete_processing_history(self, processing_history_service, case_document):
        """Soft deleting a history entry should mark it as deleted."""
        from document_processing.repositories.processing_history_repository import ProcessingHistoryRepository
        
        history = ProcessingHistoryRepository.create_history_entry(
            case_document=case_document,
            action="job_created",
            status="success",
            message="Test history entry"
        )
        initial_version = history.version
        
        deleted = ProcessingHistoryRepository.soft_delete_history_entry(
            history,
            version=initial_version
        )
        
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None
        assert deleted.version == initial_version + 1

    def test_soft_delete_filters_from_selector(self, processing_history_service, case_document):
        """Soft-deleted history entries should not appear in selectors."""
        from document_processing.repositories.processing_history_repository import ProcessingHistoryRepository
        
        history = ProcessingHistoryRepository.create_history_entry(
            case_document=case_document,
            action="job_created",
            status="success",
            message="Test history entry"
        )
        
        # History should be visible before deletion
        found = ProcessingHistorySelector.get_by_id(str(history.id))
        assert found is not None
        
        # Soft delete
        ProcessingHistoryRepository.soft_delete_history_entry(
            history,
            version=history.version
        )
        
        # History should not be visible after deletion
        from document_processing.models.processing_history import ProcessingHistory
        with pytest.raises(ProcessingHistory.DoesNotExist):
            ProcessingHistorySelector.get_by_id(str(history.id))
