"""
Repository for DocumentChunk write operations.
"""
from typing import List
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """Repository for DocumentChunk write operations."""

    @staticmethod
    def soft_delete_document_chunk(chunk: DocumentChunk, version: int = None) -> DocumentChunk:
        """Soft delete a document chunk with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(chunk, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DocumentChunk.objects.filter(
                id=chunk.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentChunk.objects.filter(id=chunk.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document chunk not found.")
                raise ValidationError(
                    f"Document chunk was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentChunk.objects.get(id=chunk.id)

    @staticmethod
    def delete_document_chunk(chunk: DocumentChunk, version: int = None):
        """
        Delete a document chunk.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        DocumentChunkRepository.soft_delete_document_chunk(chunk, version=version)
    
    @staticmethod
    def update_embedding(chunk: DocumentChunk, embedding: List[float], version: int = None) -> DocumentChunk:
        """
        Update the embedding for a document chunk.
        
        Args:
            chunk: DocumentChunk instance
            embedding: Embedding vector (1536 dimensions)
        """
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(embedding)}")

        with transaction.atomic():
            expected_version = version if version is not None else getattr(chunk, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DocumentChunk.objects.filter(
                id=chunk.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                embedding=embedding,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentChunk.objects.filter(id=chunk.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document chunk not found.")
                raise ValidationError(
                    f"Document chunk was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentChunk.objects.get(id=chunk.id)
    
    @staticmethod
    def bulk_delete_chunks(chunks: List[DocumentChunk]):
        """
        Bulk delete document chunks.
        
        Args:
            chunks: List of DocumentChunk instances to delete
        """
        if not chunks:
            return

        # NOTE: bulk operations can't reliably provide per-row conflict detection without a
        # client-supplied expected version for each row. For internal cleanup operations,
        # we prefer a single set-based soft delete with a version bump.
        chunk_ids = [chunk.id for chunk in chunks]
        now_ts = timezone.now()
        DocumentChunk.objects.filter(id__in=chunk_ids, is_deleted=False).update(
            is_deleted=True,
            deleted_at=now_ts,
            updated_at=now_ts,
            version=F("version") + 1,
        )