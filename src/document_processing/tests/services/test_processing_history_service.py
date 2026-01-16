"""
Tests for ProcessingHistoryService.

All tests create and mutate state through services (no direct model access).
"""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.django_db
class TestProcessingHistoryService:
    def test_create_history_entry_happy_path(self, processing_history_service, case_document):
        history = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
            message="Created",
            metadata={"k": "v"},
            processing_time_ms=123,
        )
        assert history is not None
        assert str(history.case_document_id) == str(case_document.id)
        assert history.action == "job_created"
        assert history.status == "success"

    def test_create_history_entry_with_job_and_user(
        self,
        processing_history_service,
        processing_job_service,
        case_document,
        admin_user,
    ):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        history = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            processing_job_id=str(job.id),
            user_id=str(admin_user.id),
            action="job_started",
            status="success",
            message="Started",
        )
        assert history is not None
        assert history.processing_job_id == job.id
        assert history.user_id == admin_user.id

    def test_create_history_entry_case_document_not_found_returns_none(self, processing_history_service, monkeypatch):
        from document_handling.selectors import case_document_selector as case_document_selector_module

        monkeypatch.setattr(
            case_document_selector_module.CaseDocumentSelector,
            "get_by_id",
            lambda *_args, **_kwargs: None,
            raising=True,
        )
        history = processing_history_service.create_history_entry(
            case_document_id=str(uuid4()),
            action="job_created",
            status="success",
        )
        assert history is None

    def test_get_by_id_not_found_returns_none(self, processing_history_service):
        assert processing_history_service.get_by_id(str(uuid4())) is None

    def test_get_by_id_returns_entry(self, processing_history_service, case_document):
        created = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        found = processing_history_service.get_by_id(str(created.id))
        assert found is not None
        assert str(found.id) == str(created.id)

    def test_get_all_returns_queryset(self, processing_history_service, case_document):
        processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        qs = processing_history_service.get_all()
        assert qs.count() >= 1

    def test_get_by_case_document(self, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        qs = processing_history_service.get_by_case_document(str(case_document.id))
        assert qs.filter(id=entry.id).exists() is True

    def test_get_by_processing_job(self, processing_history_service, processing_job_service, case_document):
        job = processing_job_service.create_processing_job(case_document_id=str(case_document.id), processing_type="ocr")
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            processing_job_id=str(job.id),
            action="job_started",
            status="success",
        )
        qs = processing_history_service.get_by_processing_job(str(job.id))
        assert qs.filter(id=entry.id).exists() is True

    def test_get_by_action_and_status(self, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_failed",
            status="failure",
            error_type="x",
        )
        by_action = processing_history_service.get_by_action("job_failed")
        assert by_action.filter(id=entry.id).exists() is True
        by_status = processing_history_service.get_by_status("failure")
        assert by_status.filter(id=entry.id).exists() is True

    def test_delete_history_entry_paid_case_success(self, processing_history_service, case_document):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        assert processing_history_service.delete_history_entry(str(entry.id)) is True

    def test_delete_history_entry_blocked_without_payment_returns_false(
        self, processing_history_service, case_document, monkeypatch
    ):
        entry = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        from payments.helpers import payment_validator as payment_validator_module

        monkeypatch.setattr(
            payment_validator_module.PaymentValidator,
            "validate_case_has_payment",
            lambda *_args, **_kwargs: (False, "Payment required"),
            raising=True,
        )
        assert processing_history_service.delete_history_entry(str(entry.id)) is False

    def test_delete_history_entry_not_found_returns_false(self, processing_history_service):
        assert processing_history_service.delete_history_entry(str(uuid4())) is False

    def test_get_by_filters_and_limit(self, processing_history_service, case_document):
        e1 = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        _e2 = processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
        )
        qs = processing_history_service.get_by_filters(case_document_id=str(case_document.id), action="job_created")
        assert qs.filter(id=e1.id).exists() is True

        limited = processing_history_service.get_by_filters(case_document_id=str(case_document.id), limit=1)
        assert len(list(limited)) == 1

    def test_get_statistics_returns_expected_shape(self, processing_history_service, case_document):
        processing_history_service.create_history_entry(
            case_document_id=str(case_document.id),
            action="job_created",
            status="success",
            processing_time_ms=10,
        )
        stats = processing_history_service.get_statistics()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "by_action" in stats
        assert "by_status" in stats

