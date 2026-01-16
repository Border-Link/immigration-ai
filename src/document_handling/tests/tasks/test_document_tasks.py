"""
Tests for document_handling.tasks.document_tasks.

We do not execute Celery asynchronously; we invoke the task's run() method
and mock downstream services for deterministic behavior.
"""

import pytest

from document_handling.tasks.document_tasks import process_document_task


@pytest.mark.django_db
class TestProcessDocumentTask:
    def test_document_not_found_returns_error(self, monkeypatch):
        monkeypatch.setattr(
            "document_handling.tasks.document_tasks.CaseDocumentSelector.get_by_id",
            lambda *_: None,
            raising=True,
        )
        result = process_document_task.run("missing-id")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_payment_invalid_sets_rejected_and_returns_error(self, monkeypatch):
        doc = type("Doc", (), {"id": "d", "case": type("Case", (), {"id": "c"})(), "file_path": "x", "mime_type": "application/pdf", "document_type": None, "file_name": "x.pdf", "file_size": 1})()
        monkeypatch.setattr("document_handling.tasks.document_tasks.CaseDocumentSelector.get_by_id", lambda *_: doc, raising=True)

        from payments.helpers import payment_validator

        monkeypatch.setattr(payment_validator.PaymentValidator, "validate_case_has_payment", lambda *_a, **_k: (False, "payment required"), raising=True)
        # repository update_status is used in this branch (imported lazily inside the task)
        updated = {"status": None}
        from document_handling.repositories.case_document_repository import CaseDocumentRepository

        monkeypatch.setattr(CaseDocumentRepository, "update_status", lambda _doc, status: updated.update({"status": status}) or _doc, raising=True)
        result = process_document_task.run("d")
        assert result["success"] is False
        assert updated["status"] == "rejected"

