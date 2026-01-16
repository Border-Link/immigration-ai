import builtins
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_decisions.services.ai_reasoning_service import AIReasoningService


@pytest.mark.django_db
class TestAIReasoningService:
    def test_construct_query_uses_facts_or_fallback(self):
        assert AIReasoningService._construct_query({}).strip() == "immigration eligibility requirements"
        q = AIReasoningService._construct_query({"visa_type": "US_TEST", "age": 30, "country": "US"})
        assert "visa type: US_TEST" in q
        assert "age: 30" in q

    def test_extract_citations_from_response(self):
        text = "See Source: https://example.com and Context 1 for details."
        citations = AIReasoningService._extract_citations(text)
        assert any(c["type"] == "url" for c in citations)
        assert any(c["type"] == "context" for c in citations)

    def test_retrieve_context_returns_empty_when_embedding_missing(self, monkeypatch):
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.EmbeddingService.generate_embedding",
            MagicMock(return_value=[]),
        )
        ctx = AIReasoningService.retrieve_context(case_facts={"age": 30})
        assert ctx == []

    def test_retrieve_context_formats_chunks_and_similarity(self, monkeypatch):
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.EmbeddingService.generate_embedding",
            MagicMock(return_value=[0.0] * 1536),
        )

        # Build a chunk-like object with the attributes used by AIReasoningService.
        chunk = SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            chunk_text="Chunk text",
            metadata={"visa_code": "US_TEST"},
            distance=0.2,
            document_version=SimpleNamespace(
                source_document=SimpleNamespace(source_url="https://example.com/doc")
            ),
        )
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.PgVectorService.search_similar",
            MagicMock(return_value=[chunk]),
        )

        ctx = AIReasoningService.retrieve_context(case_facts={"age": 30}, visa_code="US_TEST", similarity_threshold=0.0)
        assert len(ctx) == 1
        assert ctx[0]["text"] == "Chunk text"
        assert ctx[0]["source"] == "https://example.com/doc"
        assert 0.0 <= ctx[0]["similarity"] <= 1.0

    def test_call_llm_missing_openai_package_tracks_failure(self, monkeypatch):
        track = MagicMock()
        monkeypatch.setattr("ai_decisions.services.ai_reasoning_service.track_ai_reasoning", track)

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "openai":
                raise ImportError("No module named openai")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError):
            AIReasoningService.call_llm("prompt")

        assert track.call_count >= 1

    def test_call_llm_missing_api_key_tracks_failure(self, monkeypatch):
        track = MagicMock()
        monkeypatch.setattr("ai_decisions.services.ai_reasoning_service.track_ai_reasoning", track)

        class FakeClient:
            def __init__(self, api_key):
                self.api_key = api_key

        monkeypatch.setitem(__import__("sys").modules, "openai", types.SimpleNamespace(OpenAI=FakeClient))

        from ai_decisions.services import ai_reasoning_service as ai_reasoning_service_module

        monkeypatch.setattr(ai_reasoning_service_module.settings, "OPENAI_API_KEY", None, raising=False)

        with pytest.raises(ValueError):
            AIReasoningService.call_llm("prompt")

        assert track.call_count >= 1

    def test_call_llm_success_extracts_citations_and_tokens(self, monkeypatch):
        track = MagicMock()
        monkeypatch.setattr("ai_decisions.services.ai_reasoning_service.track_ai_reasoning", track)

        class FakeUsage:
            total_tokens = 30
            prompt_tokens = 10
            completion_tokens = 20

        class FakeChoice:
            message = SimpleNamespace(content="Likely eligible. See https://example.com. Context 1.")

        class FakeResponse:
            choices = [FakeChoice()]
            usage = FakeUsage()

        class FakeCompletions:
            def create(self, **kwargs):
                return FakeResponse()

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            def __init__(self, api_key):
                self.chat = FakeChat()

        monkeypatch.setitem(__import__("sys").modules, "openai", types.SimpleNamespace(OpenAI=FakeClient))

        from ai_decisions.services import ai_reasoning_service as ai_reasoning_service_module

        monkeypatch.setattr(ai_reasoning_service_module.settings, "OPENAI_API_KEY", "test-key", raising=False)

        result = AIReasoningService.call_llm("prompt", model="gpt-4", temperature=0.0)
        assert "response" in result and "citations" in result
        assert result["tokens_used"] == 30
        assert any(c["type"] == "url" for c in result["citations"])

    def test_run_ai_reasoning_payment_blocked(self, monkeypatch, paid_case):
        case, _payment = paid_case
        monkeypatch.setattr(
            "immigration_cases.selectors.case_selector.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(False, "blocked")),
        )

        out = AIReasoningService.run_ai_reasoning(case_id=str(case.id), case_facts={"age": 30})
        assert out["success"] is False
        assert out["error"] == "blocked"

    def test_run_ai_reasoning_success_happy_path(self, monkeypatch, paid_case):
        case, _payment = paid_case
        monkeypatch.setattr(
            "immigration_cases.selectors.case_selector.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.AIReasoningService.retrieve_context",
            MagicMock(return_value=[{"chunk_id": "c1", "text": "ctx", "similarity": 0.9}]),
        )
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.AIReasoningService.construct_prompt",
            MagicMock(return_value="prompt"),
        )
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.AIReasoningService.call_llm",
            MagicMock(return_value={"response": "Likely", "model": "gpt-4", "tokens_used": 20, "citations": []}),
        )
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.AIReasoningLogService.create_reasoning_log",
            MagicMock(return_value=SimpleNamespace(id="log1")),
        )

        # Patch DocumentChunk lookup used for citation creation.
        fake_doc_chunk = SimpleNamespace(document_version=SimpleNamespace(id="dv1"))
        fake_manager = SimpleNamespace(
            select_related=MagicMock(return_value=SimpleNamespace(get=MagicMock(return_value=fake_doc_chunk)))
        )
        monkeypatch.setattr(
            "data_ingestion.models.document_chunk.DocumentChunk.objects",
            fake_manager,
        )
        monkeypatch.setattr(
            "ai_decisions.services.ai_reasoning_service.AICitationService.create_citation",
            MagicMock(return_value=SimpleNamespace(id="c1")),
        )

        out = AIReasoningService.run_ai_reasoning(case_id=str(case.id), case_facts={"age": 30})
        assert out["success"] is True
        assert out["reasoning_log_id"] == "log1"
        assert out["model"] == "gpt-4"

