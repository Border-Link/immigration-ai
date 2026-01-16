from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_decisions.services.vector_db_service import PgVectorService


class _FakeQS:
    def __init__(self):
        self._calls = []

    def filter(self, **kwargs):
        self._calls.append(("filter", kwargs))
        return self

    def annotate(self, **kwargs):
        self._calls.append(("annotate", kwargs))
        return self

    def order_by(self, *args):
        self._calls.append(("order_by", args))
        return self

    def __getitem__(self, item):
        # slicing returns list(...) in PgVectorService.search_similar
        return [SimpleNamespace(id="c1")]

    def delete(self):
        return (2, {})

    def calls(self):
        return self._calls


class TestPgVectorService:
    def test_store_chunks_mismatch_raises(self):
        with pytest.raises(ValueError):
            PgVectorService.store_chunks(
                document_version=SimpleNamespace(id="dv1"),
                chunks=[{"text": "a", "metadata": {}}],
                embeddings=[[0.0] * 1536, [0.0] * 1536],
            )

    def test_store_chunks_skips_invalid_embedding_dimensions(self, monkeypatch):
        created_chunks = []

        def _fake_create(**kwargs):
            created = SimpleNamespace(**kwargs)
            created_chunks.append(created)
            return created

        monkeypatch.setattr(
            "ai_decisions.services.vector_db_service.DocumentChunk.objects",
            SimpleNamespace(create=_fake_create),
        )
        monkeypatch.setattr("ai_decisions.services.vector_db_service.bump_namespace", MagicMock())

        created = PgVectorService.store_chunks(
            document_version=SimpleNamespace(id="dv1"),
            chunks=[
                {"text": "good", "metadata": {"chunk_index": 0}},
                {"text": "bad", "metadata": {"chunk_index": 1}},
            ],
            embeddings=[
                [0.0] * 1536,
                [0.0] * 10,  # invalid dims -> should be skipped
            ],
        )
        assert len(created) == 1
        assert created_chunks[0].chunk_text == "good"

    def test_search_similar_invalid_embedding_returns_empty(self):
        assert PgVectorService.search_similar(query_embedding=[]) == []
        assert PgVectorService.search_similar(query_embedding=[0.0] * 10) == []

    def test_search_similar_builds_query_and_returns_results(self, monkeypatch):
        qs = _FakeQS()
        monkeypatch.setattr(
            "ai_decisions.services.vector_db_service.DocumentChunk.objects",
            SimpleNamespace(filter=MagicMock(return_value=qs)),
        )
        monkeypatch.setattr("ai_decisions.services.vector_db_service.CosineDistance", MagicMock(return_value="DIST"))

        out = PgVectorService.search_similar(
            query_embedding=[0.0] * 1536,
            limit=3,
            filters={"visa_code": "US_TEST"},
            similarity_threshold=0.7,
            document_version_id="dv1",
        )
        assert isinstance(out, list)
        assert len(out) == 1

        # Ensure metadata filter was applied and distance threshold filter was applied.
        filter_calls = [c for c in qs.calls() if c[0] == "filter"]
        assert any("metadata__contains" in call[1] for call in filter_calls)
        assert any("distance__lte" in call[1] for call in filter_calls)

    def test_delete_chunks_by_document_version_bumps_namespace(self, monkeypatch):
        qs = _FakeQS()
        monkeypatch.setattr(
            "ai_decisions.services.vector_db_service.DocumentChunk.objects",
            SimpleNamespace(filter=MagicMock(return_value=qs)),
        )
        bump = MagicMock()
        monkeypatch.setattr("ai_decisions.services.vector_db_service.bump_namespace", bump)

        deleted = PgVectorService.delete_chunks_by_document_version(SimpleNamespace(id="dv1"))
        assert deleted == 2
        assert bump.call_count == 1

    def test_update_chunks_for_document_version_deletes_then_creates(self, monkeypatch):
        delete_mock = MagicMock(return_value=1)
        store_mock = MagicMock(return_value=[SimpleNamespace(id="c1")])
        monkeypatch.setattr("ai_decisions.services.vector_db_service.PgVectorService.delete_chunks_by_document_version", delete_mock)
        monkeypatch.setattr("ai_decisions.services.vector_db_service.PgVectorService.store_chunks", store_mock)

        out = PgVectorService.update_chunks_for_document_version(
            document_version=SimpleNamespace(id="dv1"),
            chunks=[{"text": "x", "metadata": {"chunk_index": 0}}],
            embeddings=[[0.0] * 1536],
        )
        assert len(out) == 1
        assert delete_mock.call_count == 1
        assert store_mock.call_count == 1

