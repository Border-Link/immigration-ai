"""
Coverage tests for urls and serializers in document_handling.

We keep these light but meaningful:
- URLConf import and expected route presence
- Serializer validation for required fields
"""

import pytest
from django.urls import resolve

from document_handling.serializers.case_document.create import CaseDocumentCreateSerializer
from document_handling.serializers.document_check.create import DocumentCheckCreateSerializer


@pytest.mark.django_db
class TestURLsAndSerializers:
    def test_urls_resolve_case_documents_list(self):
        match = resolve("/api/v1/document-handling/case-documents/")
        assert match is not None

    def test_case_document_create_serializer_requires_fields(self):
        s = CaseDocumentCreateSerializer(data={})
        assert s.is_valid() is False
        assert "case_id" in s.errors
        assert "document_type_id" in s.errors
        assert "file" in s.errors

    def test_document_check_create_serializer_requires_fields(self):
        s = DocumentCheckCreateSerializer(data={})
        assert s.is_valid() is False
        assert "case_document_id" in s.errors
        assert "check_type" in s.errors
        assert "result" in s.errors

