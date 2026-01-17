import uuid
from django.db import models
from pgvector.django import VectorField
from .document_version import DocumentVersion


class DocumentChunk(models.Model):
    """
    Stores document chunks with vector embeddings for RAG retrieval.
    Each chunk represents a portion of a document version with its embedding.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    # Link to source document version
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='chunks',
        db_index=True,
        help_text="Document version this chunk belongs to"
    )
    
    # Chunk content
    chunk_text = models.TextField(
        help_text="Text content of this chunk"
    )
    
    chunk_index = models.IntegerField(
        default=0,
        help_text="Index of this chunk within the document (0-based)"
    )
    
    # Vector embedding (1536 dimensions for OpenAI ada-002)
    embedding = VectorField(
        dimensions=1536,  # OpenAI text-embedding-ada-002 dimension
        null=True,
        blank=True,
        help_text="Vector embedding for semantic search"
    )
    
    # Metadata for filtering
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (visa_code, effective_date, jurisdiction, etc.)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'document_chunks'
        ordering = ['document_version', 'chunk_index']
        indexes = [
            models.Index(fields=['document_version', 'chunk_index']),
        ]
        verbose_name_plural = 'Document Chunks'
        # Note: HNSW index for embedding will be created in a separate migration
        # CREATE INDEX document_chunks_embedding_idx ON document_chunks USING hnsw (embedding vector_cosine_ops);

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document_version.id}"

