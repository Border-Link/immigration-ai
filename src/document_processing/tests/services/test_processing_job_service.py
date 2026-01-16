"""
Tests for ProcessingJobService.

All tests create and mutate state through services (no direct model access).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestProcessingJobService:
    def test_create_processing_job_happy_path(
        self,
        processing_job_service,
        case_document,
        admin_user,
    ):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            priority=7,
            max_retries=3,
            celery_task_id="celery_test_001",
            created_by_id=str(admin_user.id),
            metadata={"source": "test"},
        )
        assert job is not None
        assert str(job.case_document_id) == str(case_document.id)
        assert job.processing_type == "ocr"
        assert job.priority == 7
        assert job.max_retries == 3
        assert job.celery_task_id == "celery_test_001"
        assert job.created_by_id == admin_user.id

    def test_create_processing_job_case_document_not_found_returns_none(self, processing_job_service, monkeypatch):
        from document_handling.selectors import case_document_selector as case_document_selector_module

        monkeypatch.setattr(
            case_document_selector_module.CaseDocumentSelector,
            "get_by_id",
            lambda *_args, **_kwargs: None,
            raising=True,
        )
        job = processing_job_service.create_processing_job(
            case_document_id=str(uuid4()),
            processing_type="ocr",
        )
        assert job is None

    def test_create_processing_job_payment_blocked_returns_none(
        self,
        processing_job_service,
        case_document,
        monkeypatch,
    ):
        from payments.helpers import payment_validator as payment_validator_module

        monkeypatch.setattr(
            payment_validator_module.PaymentValidator,
            "validate_case_has_payment",
            lambda *_args, **_kwargs: (False, "Payment required"),
            raising=True,
        )
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
        )
        assert job is None

    def test_get_by_id_not_found_returns_none(self, processing_job_service):
        job = processing_job_service.get_by_id(str(uuid4()))
        assert job is None

    def test_get_by_id_returns_job(self, processing_job_service, case_document):
        created = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id),
            processing_type="ocr",
            celery_task_id="celery_test_002",
        )
        found = processing_job_service.get_by_id(str(created.id))
        assert found is not None
        assert str(found.id) == str(created.id)

    def test_get_all_returns_queryset(self, processing_job_service, case_document):
        processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        jobs = processing_job_service.get_all()
        assert jobs.count() >= 1

    def test_get_by_case_document(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        jobs = processing_job_service.get_by_case_document(str(case_document.id))
        assert jobs.count() >= 1
        assert str(jobs.first().id) == str(job.id)

    def test_get_by_status(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(job.id), "queued")
        queued = processing_job_service.get_by_status("queued")
        assert queued.filter(id=job.id).exists() is True

    def test_get_by_processing_type(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="validation"
        )
        by_type = processing_job_service.get_by_processing_type("validation")
        assert by_type.filter(id=job.id).exists() is True

    def test_get_by_celery_task_id(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", celery_task_id="celery_abc"
        )
        found = processing_job_service.get_by_celery_task_id("celery_abc")
        assert found is not None
        assert str(found.id) == str(job.id)
        assert processing_job_service.get_by_celery_task_id("missing") is None

    def test_update_processing_job_happy_path(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        updated = processing_job_service.update_processing_job(str(job.id), priority=9, error_type="x")
        assert updated is not None
        assert updated.priority == 9
        assert updated.error_type == "x"

    def test_update_processing_job_invalid_status_transition_returns_none(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        # pending -> completed is invalid per StatusTransitionValidator
        updated = processing_job_service.update_processing_job(str(job.id), status="completed")
        assert updated is None

    def test_update_processing_job_payment_blocked_returns_none(self, processing_job_service, case_document, monkeypatch):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        from payments.helpers import payment_validator as payment_validator_module

        monkeypatch.setattr(
            payment_validator_module.PaymentValidator,
            "validate_case_has_payment",
            lambda *_args, **_kwargs: (False, "Payment required"),
            raising=True,
        )
        updated = processing_job_service.update_processing_job(str(job.id), priority=2)
        assert updated is None

    def test_update_status_sets_error_fields(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(job.id), "queued")
        updated = processing_job_service.update_status(
            str(job.id), "failed", error_message="boom", error_type="runtime_error"
        )
        assert updated is not None
        assert updated.status == "failed"
        assert updated.error_message == "boom"
        assert updated.error_type == "runtime_error"
        assert updated.completed_at is not None

    def test_increment_retry_count(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", max_retries=3
        )
        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        processing_job_service.update_status(str(job.id), "failed")
        updated = processing_job_service.increment_retry_count(str(job.id))
        assert updated is not None
        assert updated.retry_count == 1

    def test_delete_processing_job_success_and_not_found(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        assert processing_job_service.delete_processing_job(str(job.id)) is True
        assert processing_job_service.delete_processing_job(str(uuid4())) is False

    def test_get_by_filters_and_retry_exceeded(self, processing_job_service, case_document):
        job1 = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="ocr", priority=3, max_retries=1
        )
        job2 = processing_job_service.create_processing_job(
            case_document_id=str(case_document.id), processing_type="validation", priority=9, max_retries=5
        )
        processing_job_service.update_status(str(job1.id), "queued")
        processing_job_service.update_status(str(job1.id), "processing")
        processing_job_service.update_status(str(job1.id), "failed")
        processing_job_service.update_processing_job(str(job1.id), retry_count=1)

        qs = processing_job_service.get_by_filters(processing_type="ocr", min_priority=1)
        assert qs.filter(id=job1.id).exists() is True
        assert qs.filter(id=job2.id).exists() is False

        exceeded = processing_job_service.get_by_filters(max_retries_exceeded=True)
        assert exceeded.filter(id=job1.id).exists() is True

        not_exceeded = processing_job_service.get_by_filters(max_retries_exceeded=False)
        assert not_exceeded.filter(id=job1.id).exists() is False

    def test_get_statistics_returns_expected_shape(self, processing_job_service, case_document):
        processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        stats = processing_job_service.get_statistics()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "by_status" in stats
        assert "by_type" in stats

    def test_update_cost_tracking_sets_total(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        updated = processing_job_service.update_cost_tracking(
            job_id=str(job.id),
            llm_tokens_used=1200,
            llm_cost_usd=Decimal("0.012345"),
            ocr_cost_usd=Decimal("0.500000"),
        )
        assert updated is not None
        assert updated.llm_tokens_used == 1200
        assert str(updated.llm_cost_usd) == "0.012345"
        assert str(updated.ocr_cost_usd) == "0.500000"
        assert str(updated.total_cost_usd) == "0.512345"

    def test_processing_timestamps_auto_set_on_status(self, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        assert job.started_at is None
        processing_job_service.update_status(str(job.id), "queued")
        updated = processing_job_service.update_status(str(job.id), "processing")
        assert updated.started_at is not None
        completed = processing_job_service.update_status(str(job.id), "completed")
        assert completed.completed_at is not None

    def test_timeout_detector_compatibility_setup(self, processing_job_service, case_document):
        """
        Sanity: create an old 'processing' job and ensure service update can backdate started_at
        without direct ORM usage (used by timeout-service tests).
        """
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        processing_job_service.update_status(str(job.id), "queued")
        processing_job_service.update_status(str(job.id), "processing")
        old_started = timezone.now() - timedelta(hours=3)
        updated = processing_job_service.update_processing_job(str(job.id), started_at=old_started)
        assert updated is not None
        assert updated.started_at <= old_started

