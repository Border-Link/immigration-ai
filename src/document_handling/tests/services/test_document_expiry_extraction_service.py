"""
Tests for DocumentExpiryExtractionService.
"""

import pytest

from datetime import date

from document_handling.services.document_expiry_extraction_service import DocumentExpiryExtractionService


@pytest.mark.django_db
class TestDocumentExpiryExtractionService:
    def test_extract_expiry_date_insufficient_text(self):
        d, conf, meta, err = DocumentExpiryExtractionService.extract_expiry_date("x")
        assert d is None
        assert err is not None

    def test_extract_expiry_date_invalid_date_format(self, monkeypatch):
        monkeypatch.setattr(
            DocumentExpiryExtractionService,
            "_extract_with_llm",
            lambda **kwargs: {"expiry_date": "not-a-date", "confidence": 0.8, "metadata": {}},
            raising=True,
        )
        d, conf, meta, err = DocumentExpiryExtractionService.extract_expiry_date("some sufficiently long ocr text", "passport", "x.pdf")
        assert d is None
        assert conf == 0.8
        assert err is not None

    def test_is_expired_and_days_until_expiry(self):
        today = date.today()
        assert DocumentExpiryExtractionService.is_expired(today) is False
        assert DocumentExpiryExtractionService.is_expired(today, buffer_days=1) is True
        assert DocumentExpiryExtractionService.days_until_expiry(today) == 0
        assert DocumentExpiryExtractionService.days_until_expiry(None) is None

