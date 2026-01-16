"""
Tests for DocumentContentValidationService.

We mock selectors and LLM calls to avoid external dependencies and to cover
edge/failure scenarios.
"""

import pytest

from document_handling.services.document_content_validation_service import DocumentContentValidationService


@pytest.mark.django_db
class TestDocumentContentValidationService:
    def test_validate_content_case_document_not_found(self, monkeypatch):
        from document_handling.selectors.case_document_selector import CaseDocumentSelector

        monkeypatch.setattr(CaseDocumentSelector, "get_by_id", lambda *_: None, raising=True)
        status, details, err = DocumentContentValidationService.validate_content("missing-id", ocr_text="some text")
        assert status == "pending"
        assert err is not None

    def test_validate_content_no_case_facts(self, monkeypatch):
        doc = type("Doc", (), {"case": object(), "ocr_text": "some text", "document_type": None, "extracted_metadata": None})()

        class _Facts:
            def exists(self):
                return False

        from document_handling.selectors.case_document_selector import CaseDocumentSelector

        monkeypatch.setattr(CaseDocumentSelector, "get_by_id", lambda *_: doc, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_content_validation_service.CaseFactSelector.get_by_case",
            lambda *_: _Facts(),
            raising=True,
        )
        status, details, err = DocumentContentValidationService.validate_content("doc-id", ocr_text="some long enough text")
        assert status == "pending"
        assert err is not None

    def test_validate_content_insufficient_ocr_text(self, monkeypatch):
        doc = type("Doc", (), {"case": object(), "ocr_text": "x", "document_type": None, "extracted_metadata": None})()

        class _Facts(list):
            def exists(self):
                return True

        from document_handling.selectors.case_document_selector import CaseDocumentSelector

        monkeypatch.setattr(CaseDocumentSelector, "get_by_id", lambda *_: doc, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_content_validation_service.CaseFactSelector.get_by_case",
            lambda *_: _Facts([type("F", (), {"fact_key": "name", "fact_value": "A"})()]),
            raising=True,
        )
        status, details, err = DocumentContentValidationService.validate_content("doc-id")
        assert status == "pending"
        assert err is not None

    def test_validate_content_llm_failure_returns_pending(self, monkeypatch):
        doc = type(
            "Doc",
            (),
            {"case": object(), "ocr_text": "some long enough ocr text", "document_type": None, "extracted_metadata": None},
        )()

        class _Facts(list):
            def exists(self):
                return True

        from document_handling.selectors.case_document_selector import CaseDocumentSelector

        monkeypatch.setattr(CaseDocumentSelector, "get_by_id", lambda *_: doc, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_content_validation_service.CaseFactSelector.get_by_case",
            lambda *_: _Facts([type("F", (), {"fact_key": "name", "fact_value": "A"})()]),
            raising=True,
        )
        monkeypatch.setattr(DocumentContentValidationService, "_validate_with_llm", lambda **_: None, raising=True)
        status, details, err = DocumentContentValidationService.validate_content("doc-id")
        assert status == "pending"
        assert err is not None

    def test_validate_content_success(self, monkeypatch):
        doc = type(
            "Doc",
            (),
            {
                "case": object(),
                "ocr_text": "some long enough ocr text",
                "document_type": type("DT", (), {"code": "passport"})(),
                "extracted_metadata": {"x": 1},
            },
        )()

        class _Facts(list):
            def exists(self):
                return True

        from document_handling.selectors.case_document_selector import CaseDocumentSelector

        monkeypatch.setattr(CaseDocumentSelector, "get_by_id", lambda *_: doc, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_content_validation_service.CaseFactSelector.get_by_case",
            lambda *_: _Facts([type("F", (), {"fact_key": "name", "fact_value": "A"})()]),
            raising=True,
        )
        monkeypatch.setattr(
            DocumentContentValidationService,
            "_validate_with_llm",
            lambda **_: {"status": "passed", "details": {"matched_fields": ["name"]}},
            raising=True,
        )
        status, details, err = DocumentContentValidationService.validate_content("doc-id")
        assert status == "passed"
        assert isinstance(details, dict)
        assert err is None

    def test_get_validation_summary(self):
        assert DocumentContentValidationService.get_validation_summary(None) == "Validation pending"
        summary = DocumentContentValidationService.get_validation_summary(
            {
                "matched_fields": ["a", "b"],
                "mismatched_fields": ["c"],
                "missing_fields": [],
                "summary": "ok",
            }
        )
        assert "Matched:" in summary

