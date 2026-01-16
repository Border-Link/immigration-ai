import builtins
import types
from unittest.mock import MagicMock

import pytest

from ai_decisions.services.embedding_service import EmbeddingService


@pytest.mark.django_db
class TestEmbeddingService:
    def test_chunk_document_empty(self):
        assert EmbeddingService.chunk_document("") == []
        assert EmbeddingService.chunk_document("   \n ") == []

    def test_chunk_document_respects_boundaries_and_metadata(self):
        text = (
            "Sentence one. Sentence two!\n"
            "Sentence three? Sentence four. " * 50
        )
        chunks = EmbeddingService.chunk_document(text, chunk_size=200, overlap=20)
        assert chunks
        assert chunks[0]["metadata"]["chunk_index"] == 0
        assert all("text" in c and "metadata" in c for c in chunks)
        assert chunks[-1]["metadata"]["chunk_index"] == len(chunks) - 1

        # Overlap should imply later chunks start before prior chunk ends (in char offsets).
        if len(chunks) >= 2:
            assert chunks[1]["metadata"]["start_char"] < chunks[0]["metadata"]["end_char"]

    def test_validate_embedding(self):
        assert EmbeddingService.validate_embedding([]) is False
        assert EmbeddingService.validate_embedding([0.0] * 10) is False
        assert EmbeddingService.validate_embedding([0.0] * EmbeddingService.EMBEDDING_DIMENSIONS) is True

    def test_generate_embeddings_empty_input(self):
        assert EmbeddingService.generate_embeddings([]) == []

    def test_generate_embeddings_missing_openai_package(self, monkeypatch):
        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "openai":
                raise ImportError("No module named openai")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError):
            EmbeddingService.generate_embeddings(["hello"])

    def test_generate_embeddings_missing_api_key(self, monkeypatch):
        # Provide a fake openai module so we get to the API key validation branch.
        fake_openai = types.SimpleNamespace(OpenAI=MagicMock(name="OpenAI"))
        monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)

        from ai_decisions.services import embedding_service as embedding_service_module

        # Ensure API key is not set
        monkeypatch.setattr(embedding_service_module.settings, "OPENAI_API_KEY", None, raising=False)

        with pytest.raises(ValueError):
            EmbeddingService.generate_embeddings(["hello"])

    def test_generate_embeddings_success(self, monkeypatch):
        class FakeEmbeddingItem:
            def __init__(self, embedding):
                self.embedding = embedding

        class FakeEmbeddingsResponse:
            def __init__(self, data):
                self.data = data

        class FakeEmbeddingsAPI:
            def create(self, model, input):
                return FakeEmbeddingsResponse([FakeEmbeddingItem([0.0] * 1536) for _ in input])

        class FakeClient:
            def __init__(self, api_key):
                self.embeddings = FakeEmbeddingsAPI()

        fake_openai = types.SimpleNamespace(OpenAI=FakeClient)
        monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)

        from ai_decisions.services import embedding_service as embedding_service_module

        monkeypatch.setattr(embedding_service_module.settings, "OPENAI_API_KEY", "test-key", raising=False)

        embeddings = EmbeddingService.generate_embeddings(["a", "b"])
        assert len(embeddings) == 2
        assert all(len(vec) == 1536 for vec in embeddings)

