"""
Tests for OCRService.

We avoid external dependencies (pytesseract/boto3/google vision) and validate
fallback/error handling behavior.
"""

import pytest

from document_handling.services.ocr_service import OCRService


@pytest.mark.django_db
class TestOCRService:
    def test_extract_text_unknown_backend_returns_error(self, settings, monkeypatch):
        settings.OCR_BACKEND = "unknown_backend"
        # Avoid metrics side effects
        monkeypatch.setattr("document_handling.services.ocr_service.track_ocr_operation", lambda *a, **k: None, raising=False)

        text, metadata, err = OCRService.extract_text("case_documents/a/b/test.pdf", mime_type="application/pdf")
        assert text is None
        assert err is not None

    def test_extract_text_tesseract_missing_deps_returns_error(self, settings, monkeypatch):
        settings.OCR_BACKEND = "tesseract"
        monkeypatch.setattr("document_handling.services.ocr_service.track_ocr_operation", lambda *a, **k: None, raising=False)

        text, metadata, err = OCRService.extract_text("case_documents/a/b/test.pdf", mime_type="application/pdf")
        # In CI, pytesseract/pdf2image are typically missing; ensure defensive message
        assert text is None
        assert err is not None

