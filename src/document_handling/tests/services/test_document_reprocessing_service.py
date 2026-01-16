"""
Tests for DocumentReprocessingService.

We mock downstream integrations (OCR/LLM/tasks) and assert orchestration calls.
"""

import pytest

from document_handling.services.document_reprocessing_service import DocumentReprocessingService


@pytest.mark.django_db
class TestDocumentReprocessingService:
    def test_reprocess_ocr_document_not_found_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.CaseDocumentSelector.get_by_id",
            lambda *_: None,
            raising=True,
        )
        assert DocumentReprocessingService.reprocess_ocr("missing") is False

    def test_reprocess_ocr_payment_invalid_returns_false(self, monkeypatch):
        doc = type("Doc", (), {"id": "d", "case": object(), "file_path": "x", "mime_type": "application/pdf"})()
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        from payments.helpers import payment_validator

        monkeypatch.setattr(payment_validator.PaymentValidator, "validate_case_has_payment", lambda *_a, **_k: (False, "no pay"), raising=True)
        assert DocumentReprocessingService.reprocess_ocr("d") is False

    def test_reprocess_ocr_success_updates_doc_and_creates_check(self, monkeypatch):
        doc = type("Doc", (), {"id": "d", "case": object(), "file_path": "x", "mime_type": "application/pdf"})()
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.OCRService.extract_text",
            lambda *a, **k: ("some extracted text", {"backend": "x"}, None),
            raising=True,
        )

        updated = {}

        def _update(document_id, **fields):
            updated.update(fields)
            return object()

        created_checks = []

        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.CaseDocumentService.update_case_document",
            _update,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.DocumentCheckService.create_document_check",
            lambda **kwargs: created_checks.append(kwargs) or object(),
            raising=True,
        )
        ok = DocumentReprocessingService.reprocess_ocr("d")
        assert ok is True
        assert "ocr_text" in updated
        assert any(c["check_type"] == "ocr" for c in created_checks)

    def test_reprocess_classification_insufficient_ocr_returns_false(self, monkeypatch):
        doc = type("Doc", (), {"id": "d", "case": object(), "ocr_text": "x", "file_name": "x.pdf", "file_size": 1, "mime_type": "application/pdf"})()
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        assert DocumentReprocessingService.reprocess_classification("d") is False

    def test_reprocess_full_triggers_async_task(self, monkeypatch):
        doc = type("Doc", (), {"id": "d", "case": object()})()
        monkeypatch.setattr(
            "document_handling.services.document_reprocessing_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        called = {"delay": 0}

        # reprocess_full lazily imports the Celery task from document_handling.tasks.document_tasks
        monkeypatch.setattr(
            "document_handling.tasks.document_tasks.process_document_task.delay",
            lambda *_a, **_k: called.update({"delay": called["delay"] + 1}),
            raising=True,
        )
        ok = DocumentReprocessingService.reprocess_full("d")
        assert ok is True
        assert called["delay"] == 1

