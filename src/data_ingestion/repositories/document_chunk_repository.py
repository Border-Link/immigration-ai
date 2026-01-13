"""
Repository for DocumentChunk write operations.
"""
from typing import List
from data_ingestion.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """Repository for DocumentChunk write operations."""

    @staticmethod
    def delete_document_chunk(chunk: DocumentChunk):
        """Delete a document chunk."""
        chunk.delete()
    
    @staticmethod
    def update_embedding(chunk: DocumentChunk, embedding: List[float]):
        """
        Update the embedding for a document chunk.
        
        Args:
            chunk: DocumentChunk instance
            embedding: Embedding vector (1536 dimensions)
        """
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(embedding)}")
        
        chunk.embedding = embedding
        chunk.save(update_fields=['embedding', 'updated_at'])
    
    @staticmethod
    def bulk_delete_chunks(chunks: List[DocumentChunk]):
        """
        Bulk delete document chunks.
        
        Args:
            chunks: List of DocumentChunk instances to delete
        """
        if chunks:
            chunk_ids = [chunk.id for chunk in chunks]
            DocumentChunk.objects.filter(id__in=chunk_ids).delete()