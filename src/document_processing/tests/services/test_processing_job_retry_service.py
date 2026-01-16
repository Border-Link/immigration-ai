"""
Tests for ProcessingJobRetryService.

Notes:
- Celery task invocation is isolated by conftest autouse fixture.
- History creation is asserted via ProcessingHistoryService.
"""

from __future__ import annotations

from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from document_processing.services.processing_job_retry_service import ProcessingJobRetryService


@pytest.mark.django_db
class TestProcessingJobRetryService:
    def test_should_retry_rules(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        assert ProcessingJobRetryService.should_retry(job) is False

        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        processing_job_service.update_status(str(job.id), "failed")
        job = processing_job_service.get_by_id(str(job.id))
        assert ProcessingJobRetryService.should_retry(job) is True

        processing_job_service.update_processing_job(str(job.id), retry_count=job.max_retries)
        job = processing_job_service.get_by_id(str(job.id))
        assert ProcessingJobRetryService.should_retry(job) is False

    def test_retry_job_not_found_returns_none(self):
        assert ProcessingJobRetryService.retry_job(str(uuid4())) is None

    def test_retry_job_payment_blocked_returns_none(self, processing_job_service, case_document, monkeypatch):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        processing_job_service.update_status(str(job.id), "failed")

        from payments.helpers import payment_validator as payment_validator_module

        monkeypatch.setattr(
            payment_validator_module.PaymentValidator,
            "validate_case_has_payment",
            lambda *_args, **_kwargs: (False, "Payment required"),
            raising=True,
        )
        assert ProcessingJobRetryService.retry_job(str(job.id)) is None

    def test_retry_job_should_retry_false_returns_none(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        # Not failed -> should_retry False
        assert ProcessingJobRetryService.retry_job(str(job.id)) is None

    def test_retry_job_success_path_creates_history_and_queues_task(
        self,
        processing_job_service,
        processing_history_service,
        case_document,
        monkeypatch,
    ):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=3
        )
        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        processing_job_service.update_status(str(job.id), "failed", error_message="boom", error_type="x")

        # Ensure Celery delay exists and can be asserted
        from document_handling.tasks import document_tasks as document_tasks_module

        delay_mock = MagicMock(name="process_document_task.delay")
        monkeypatch.setattr(document_tasks_module.process_document_task, "delay", delay_mock, raising=False)

        retried = ProcessingJobRetryService.retry_job(str(job.id))
        assert retried is not None
        assert retried.status == "pending"
        assert retried.retry_count == 1
        assert retried.error_message is None
        assert retried.error_type is None

        # History entry for retry attempt created
        history_qs = processing_history_service.get_by_processing_job(str(retried.id))
        assert history_qs.filter(action="retry_attempted").exists() is True

        delay_mock.assert_called_once()

    def test_retry_job_celery_queue_failure_sets_job_failed(
        self,
        processing_job_service,
        case_document,
        monkeypatch,
    ):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=3
        )
        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        processing_job_service.update_status(str(job.id), "failed")

        # Force the Celery queueing to fail
        from document_handling.tasks import document_tasks as document_tasks_module

        def _raise(*_args, **_kwargs):
            raise RuntimeError("broker down")

        monkeypatch.setattr(document_tasks_module.process_document_task, "delay", _raise, raising=False)

        assert ProcessingJobRetryService.retry_job(str(job.id)) is None

        # Job should be set back to failed with retry_queue_failed
        updated = processing_job_service.get_by_id(str(job.id))
        assert updated is not None
        assert updated.status == "failed"
        assert updated.error_type == "retry_queue_failed"
        assert "broker down" in (updated.error_message or "")

    def test_auto_retry_failed_jobs_stats(self, processing_job_service, case_document, monkeypatch):
        eligible = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=2
        )
        maxed = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=1
        )
        for j in (eligible, maxed):
            processing_job_service.update_status(str(j.id), "queued")
            processing_job_service.update_status(str(j.id), "processing")
            processing_job_service.update_status(str(j.id), "failed")
        processing_job_service.update_processing_job(str(maxed.id), retry_count=1)

        # Make retry_job succeed only for eligible
        monkeypatch.setattr(
            ProcessingJobRetryService,
            "retry_job",
            lambda job_id: processing_job_service.update_status(job_id, "pending") if job_id == str(eligible.id) else None,
            raising=True,
        )
        stats = ProcessingJobRetryService.auto_retry_failed_jobs()
        assert stats["retried"] == 1
        assert stats["skipped"] == 1

