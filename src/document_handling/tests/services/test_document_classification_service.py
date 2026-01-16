"""
Tests for DocumentClassificationService.
"""

import pytest

from document_handling.services.document_classification_service import DocumentClassificationService


@pytest.mark.django_db
class TestDocumentClassificationService:
    def test_should_auto_classify_threshold(self):
        assert DocumentClassificationService.should_auto_classify(DocumentClassificationService.CONFIDENCE_THRESHOLD) is True
        assert DocumentClassificationService.should_auto_classify(DocumentClassificationService.CONFIDENCE_THRESHOLD - 0.01) is False

    def test_classify_document_no_active_types(self, monkeypatch):
        class _Empty:
            def exists(self):
                return False

        monkeypatch.setattr(
            "document_handling.services.document_classification_service.DocumentTypeSelector.get_all_active",
            lambda: _Empty(),
            raising=True,
        )
        doc_type_id, confidence, metadata, err = DocumentClassificationService.classify_document("some ocr text", "x.pdf")
        assert doc_type_id is None
        assert err is not None

    def test_classify_document_unknown_type_returned_by_llm(self, monkeypatch):
        # Provide active types list with known code, and have LLM return unknown code.
        class _QS:
            def __init__(self):
                self._codes = ["passport"]

            def exists(self):
                return True

            def __iter__(self):
                # minimal objects for code list
                return iter([type("DT", (), {"code": "passport"})()])

            def filter(self, code=None):
                class _F:
                    def first(self_inner):
                        return None
                return _F()

        monkeypatch.setattr(
            "document_handling.services.document_classification_service.DocumentTypeSelector.get_all_active",
            lambda: _QS(),
            raising=True,
        )
        monkeypatch.setattr(
            DocumentClassificationService,
            "_classify_with_llm",
            lambda **kwargs: {"document_type": "unknown_type", "confidence": 0.9, "metadata": {}},
            raising=True,
        )
        doc_type_id, confidence, metadata, err = DocumentClassificationService.classify_document("some ocr text", "x.pdf")
        assert doc_type_id is None
        assert confidence == 0.9
        assert err is not None

