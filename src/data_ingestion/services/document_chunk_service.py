"""
Service for DocumentChunk business logic.
"""
import logging
from typing import Optional
from data_ingestion.models.document_chunk import DocumentChunk
from data_ingestion.selectors.document_chunk_selector import DocumentChunkSelector
from data_ingestion.repositories.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger('django')


class DocumentChunkService:
    """Service for DocumentChunk business logic."""

    @staticmethod
    def get_all():
        """Get all document chunks."""
        try:
            return DocumentChunkSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document chunks: {e}")
            return DocumentChunkSelector.get_none()

    @staticmethod
    def get_by_document_version(document_version_id: str):
        """Get document chunks by document version ID."""
        try:
            return DocumentChunkSelector.get_by_document_version(document_version_id)
        except Exception as e:
            logger.error(f"Error fetching document chunks for document version {document_version_id}: {e}")
            return DocumentChunkSelector.get_none()

    @staticmethod
    def get_by_id(chunk_id: str) -> Optional[DocumentChunk]:
        """Get document chunk by ID."""
        try:
            return DocumentChunkSelector.get_by_id(chunk_id)
        except DocumentChunk.DoesNotExist:
            logger.error(f"Document chunk {chunk_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document chunk {chunk_id}: {e}")
            return None

    @staticmethod
    def delete_document_chunk(chunk_id: str) -> bool:
        """Delete a document chunk."""
        try:
            chunk = DocumentChunkSelector.get_by_id(chunk_id)
            DocumentChunkRepository.delete_document_chunk(chunk)
            return True
        except DocumentChunk.DoesNotExist:
            logger.error(f"Document chunk {chunk_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document chunk {chunk_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(document_version_id: str = None, has_embedding: bool = None):
        """Get document chunks with filters."""
        try:
            return DocumentChunkSelector.get_by_filters(
                document_version_id=document_version_id,
                has_embedding=has_embedding
            )
        except Exception as e:
            logger.error(f"Error fetching filtered document chunks: {e}")
            return DocumentChunkSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get document chunk statistics."""
        try:
            return DocumentChunkSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting document chunk statistics: {e}")
            return {}
