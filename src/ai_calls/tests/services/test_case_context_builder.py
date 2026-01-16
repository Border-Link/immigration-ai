"""
Tests for CaseContextBuilder.

We keep these unit-level by mocking selector/service dependencies from other apps.
"""

import pytest
from unittest.mock import MagicMock


class TestCaseContextBuilder:
    def test_validate_context_bundle_required_fields(self):
        from ai_calls.services.case_context_builder import CaseContextBuilder

        ok, err = CaseContextBuilder.validate_context_bundle({})
        assert ok is False
        assert "empty" in (err or "").lower()

        ok2, err2 = CaseContextBuilder.validate_context_bundle({"case_id": "1"})
        assert ok2 is False
        assert "missing required fields" in (err2 or "").lower()

        ok3, err3 = CaseContextBuilder.validate_context_bundle(
            {"case_id": "1", "case_facts": {}, "documents_summary": {}}
        )
        assert ok3 is True
        assert err3 is None

    def test_detect_restricted_topics(self):
        from ai_calls.services.case_context_builder import CaseContextBuilder

        assert CaseContextBuilder.detect_restricted_topics("") == []
        matches = CaseContextBuilder.detect_restricted_topics("I need legal advice about my case")
        assert isinstance(matches, list)

    def test_compute_context_hash_is_deterministic(self):
        from ai_calls.services.case_context_builder import CaseContextBuilder

        bundle = {"b": 1, "a": 2}
        h1 = CaseContextBuilder.compute_context_hash(bundle)
        h2 = CaseContextBuilder.compute_context_hash({"a": 2, "b": 1})
        assert h1 == h2
        assert len(h1) == 64

    def test_build_context_bundle_returns_empty_when_case_missing(self, monkeypatch):
        from ai_calls.services import case_context_builder as builder_module

        monkeypatch.setattr(builder_module.CaseSelector, "get_by_id", MagicMock(return_value=None))
        res = builder_module.CaseContextBuilder.build_context_bundle("missing")
        assert res == {}

    def test_build_context_bundle_happy_path_uses_components(self, monkeypatch):
        from ai_calls.services import case_context_builder as builder_module

        fake_case = MagicMock()
        fake_case.id = "case1"
        fake_case.jurisdiction = "US"
        fake_case.status = "draft"

        monkeypatch.setattr(builder_module.CaseSelector, "get_by_id", MagicMock(return_value=fake_case))
        monkeypatch.setattr(builder_module.CaseContextBuilder, "_get_case_facts", MagicMock(return_value={"age": 30}))
        monkeypatch.setattr(builder_module.CaseContextBuilder, "_get_documents_summary", MagicMock(return_value={"uploaded": [], "missing": [], "status": {}}))
        monkeypatch.setattr(builder_module.CaseContextBuilder, "_get_human_review_notes", MagicMock(return_value=[]))
        monkeypatch.setattr(builder_module.CaseContextBuilder, "_get_ai_findings", MagicMock(return_value={"eligibility_results": []}))
        monkeypatch.setattr(builder_module.CaseContextBuilder, "_get_rules_knowledge_for_case", MagicMock(return_value={}))

        ctx = builder_module.CaseContextBuilder.build_context_bundle("case1")
        assert ctx["case_id"] == "case1"
        assert "case_facts" in ctx
        assert "documents_summary" in ctx
        assert "allowed_topics" in ctx
        assert "restricted_topics" in ctx

