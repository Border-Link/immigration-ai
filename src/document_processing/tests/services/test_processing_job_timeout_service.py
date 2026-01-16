"""
Tests for ProcessingJobTimeoutService.

All state creation/mutation uses services (no direct model access in tests).
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone

from document_processing.services.processing_job_timeout_service import ProcessingJobTimeoutService


@pytest.mark.django_db
class TestProcessingJobTimeoutService:
    def test_detect_stuck_jobs_returns_only_old_processing_jobs(self, processing_job_service, case_document):
        # Old processing job
        old_job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr"
        )
        processing_job_service.update_status(str(old_job.id), "queued")
        processing_job_service.update_status(str(old_job.id), "processing")
        processing_job_service.update_processing_job(
            str(old_job.id), started_at=timezone.now() - timedelta(hours=5)
        )

        # Recent processing job (not stuck)
        recent_job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr"
        )
        processing_job_service.update_status(str(recent_job.id), "queued")
        processing_job_service.update_status(str(recent_job.id), "processing")
        processing_job_service.update_processing_job(
            str(recent_job.id), started_at=timezone.now() - timedelta(minutes=5)
        )

        # Non-processing job
        pending_job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr"
        )

        stuck = ProcessingJobTimeoutService.detect_stuck_jobs(timeout_minutes=60)
        stuck_ids = {str(j.id) for j in stuck}
        assert str(old_job.id) in stuck_ids
        assert str(recent_job.id) not in stuck_ids
        assert str(pending_job.id) not in stuck_ids

    def test_cancel_stuck_job_not_found_returns_false(self):
        assert ProcessingJobTimeoutService.cancel_stuck_job(str(uuid4())) is False

    def test_cancel_stuck_job_wrong_status_returns_false(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        assert ProcessingJobTimeoutService.cancel_stuck_job(str(job.id)) is False

    def test_cancel_stuck_job_marks_failed_sets_completed_and_logs_history(
        self,
        processing_job_service,
        processing_history_service,
        case_document,
    ):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        processing_job_service.update_processing_job(str(job.id), started_at=timezone.now() - timedelta(hours=2))

        ok = ProcessingJobTimeoutService.cancel_stuck_job(str(job.id), reason="Job timeout test")
        assert ok is True

        updated = processing_job_service.get_by_id(str(job.id))
        assert updated is not None
        assert updated.status == "failed"
        assert updated.error_type == "timeout"
        assert "timeout" in (updated.error_message or "").lower()
        assert updated.completed_at is not None

        history_qs = processing_history_service.get_by_processing_job(str(job.id))
        assert history_qs.filter(action="job_failed", error_type="timeout").exists() is True

    def test_cleanup_stuck_jobs_stats(self, processing_job_service, case_document, monkeypatch):
        j1 = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(j1.id), "queued")
        processing_job_service.update_status(str(j1.id), "processing")
        processing_job_service.update_processing_job(str(j1.id), started_at=timezone.now() - timedelta(hours=3))

        j2 = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(j2.id), "queued")
        processing_job_service.update_status(str(j2.id), "processing")
        processing_job_service.update_processing_job(str(j2.id), started_at=timezone.now() - timedelta(hours=3))

        # Make one cancellation fail
        original_cancel = ProcessingJobTimeoutService.cancel_stuck_job

        def _cancel(job_id: str, reason: str = "Job timeout"):
            if job_id == str(j2.id):
                return False
            return original_cancel(job_id, reason)

        monkeypatch.setattr(ProcessingJobTimeoutService, "cancel_stuck_job", _cancel, raising=True)

        stats = ProcessingJobTimeoutService.cleanup_stuck_jobs(timeout_minutes=60)
        assert stats["cancelled"] == 1
        assert stats["failed"] == 1

