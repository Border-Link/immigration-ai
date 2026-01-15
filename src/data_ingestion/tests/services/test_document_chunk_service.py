"""
Tests for DocumentChunkService.
"""

import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestDocumentChunkService:
    def test_get_all(self, document_chunks):
        from data_ingestion.services.document_chunk_service import DocumentChunkService

        qs = DocumentChunkService.get_all()
        assert qs.count() >= 1

    def test_get_by_document_version(self, document_chunks, document_version):
        from data_ingestion.services.document_chunk_service import DocumentChunkService

        qs = DocumentChunkService.get_by_document_version(str(document_version.id))
        assert qs.count() >= 1

    def test_get_by_id_success(self, document_chunks):
        from data_ingestion.services.document_chunk_service import DocumentChunkService

        chunk = document_chunks[0]
        found = DocumentChunkService.get_by_id(str(chunk.id))
        assert found is not None
        assert str(found.id) == str(chunk.id)

    def test_delete_document_chunk_success(self, document_chunks):
        from data_ingestion.services.document_chunk_service import DocumentChunkService

        chunk = document_chunks[0]
        ok = DocumentChunkService.delete_document_chunk(str(chunk.id))
        assert ok is True
        assert DocumentChunkService.get_by_id(str(chunk.id)) is None

    @patch("data_ingestion.services.document_chunk_service.DocumentChunkRepository")
    @patch("ai_decisions.services.embedding_service.EmbeddingService.generate_embedding")
    def test_regenerate_embedding_success(self, mock_generate, mock_repo, document_chunks):
        from data_ingestion.services.document_chunk_service import DocumentChunkService

        chunk = document_chunks[0]
        mock_generate.return_value = [0.0] * 1536
        ok = DocumentChunkService.regenerate_embedding(str(chunk.id), model="test-model")
        assert ok is True
        mock_repo.update_embedding.assert_called()

    @patch("ai_decisions.services.embedding_service.EmbeddingService.generate_embedding")
    def test_regenerate_embedding_invalid_embedding_length_returns_false(self, mock_generate, document_chunks):
        from data_ingestion.services.document_chunk_service import DocumentChunkService

        chunk = document_chunks[0]
        mock_generate.return_value = [0.0] * 10
        ok = DocumentChunkService.regenerate_embedding(str(chunk.id), model="test-model")
        assert ok is False

