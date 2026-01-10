"""
Repository for DocumentChunk write operations.
"""
from data_ingestion.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """Repository for DocumentChunk write operations."""

    @staticmethod
    def delete_document_chunk(chunk: DocumentChunk):
        """Delete a document chunk."""
        chunk.delete()
