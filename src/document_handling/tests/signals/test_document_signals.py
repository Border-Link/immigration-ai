"""
Tests for document_handling.signals.document_signals.

We call the signal handlers directly (unit-level) and assert orchestration
to tasks/notifications without relying on Django signal dispatch.
"""

import pytest

from document_handling.signals.document_signals import (
    handle_document_uploaded,
    handle_document_check_result,
)


@pytest.mark.django_db
class TestDocumentSignals:
    def test_handle_document_uploaded_created_triggers_processing_and_notification(self, monkeypatch, test_case):
        called = {"delay": 0, "notify": 0}

        class _Task:
            @staticmethod
            def delay(*args, **kwargs):
                called["delay"] += 1

        monkeypatch.setattr("document_handling.signals.document_signals.process_document_task", _Task, raising=False)
        monkeypatch.setattr(
            "document_handling.signals.document_signals.NotificationService.create_notification",
            lambda **kwargs: called.update({"notify": called["notify"] + 1}),
            raising=True,
        )

        doc = type("Doc", (), {"id": "d", "case": test_case})()
        handle_document_uploaded(sender=None, instance=doc, created=True)
        assert called["delay"] == 1
        assert called["notify"] == 1

    def test_handle_document_check_result_failed_triggers_notification_and_email(self, monkeypatch, test_case):
        called = {"notify": 0, "email": 0}

        monkeypatch.setattr(
            "document_handling.signals.document_signals.NotificationService.create_notification",
            lambda **kwargs: called.update({"notify": called["notify"] + 1}),
            raising=True,
        )

        class _EmailTask:
            @staticmethod
            def delay(*args, **kwargs):
                called["email"] += 1

        monkeypatch.setattr("document_handling.signals.document_signals.send_document_status_email_task", _EmailTask, raising=False)

        doc = type("Doc", (), {"id": "d", "case": test_case})()
        check = type("Check", (), {"case_document": doc, "result": "failed", "check_type": "ocr", "details": {"x": 1}, "id": "cid"})()
        handle_document_check_result(sender=None, instance=check, created=True)
        assert called["notify"] == 1
        assert called["email"] == 1

