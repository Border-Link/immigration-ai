"""
Service for DocumentChunk business logic.
"""
import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from data_ingestion.models.document_chunk import DocumentChunk
from data_ingestion.selectors.document_chunk_selector import DocumentChunkSelector
from data_ingestion.repositories.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "document_chunks"


class DocumentChunkService:
    """Service for DocumentChunk business logic."""

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")
    def get_all():
        """Get all document chunks."""
        try:
            return DocumentChunkSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document chunks: {e}")
            return DocumentChunkSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['document_version_id'], namespace=namespace, user_scope="global")
    def get_by_document_version(document_version_id: str):
        """Get document chunks by document version ID."""
        try:
            return DocumentChunkSelector.get_by_document_version(document_version_id)
        except Exception as e:
            logger.error(f"Error fetching document chunks for document version {document_version_id}: {e}")
            return DocumentChunkSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['chunk_id'], namespace=namespace, user_scope="global")
    def get_by_id(chunk_id: str) -> Optional[DocumentChunk]:
        """Get document chunk by ID."""
        try:
            chunk = DocumentChunkSelector.get_by_id(chunk_id)
            if not chunk:
                logger.error(f"Document chunk {chunk_id} not found")
                return None
            return chunk
        except Exception as e:
            logger.error(f"Error fetching document chunk {chunk_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_document_chunk(chunk_id: str) -> bool:
        """Delete a document chunk."""
        try:
            chunk = DocumentChunkSelector.get_by_id(chunk_id)
            if not chunk:
                logger.error(f"Document chunk {chunk_id} not found")
                return False
            DocumentChunkRepository.delete_document_chunk(chunk, version=getattr(chunk, "version", None))
            return True
        except Exception as e:
            logger.error(f"Error deleting document chunk {chunk_id}: {e}")
            return False

    @staticmethod
    @cache_result(timeout=300, keys=['document_version_id', 'has_embedding'], namespace=namespace, user_scope="global")
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
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get document chunk statistics."""
        try:
            return DocumentChunkSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting document chunk statistics: {e}")
            return {}
    
    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def regenerate_embedding(chunk_id: str, model: str = "text-embedding-ada-002") -> bool:
        """
        Regenerate embedding for a document chunk.
        
        Args:
            chunk_id: Document chunk ID
            model: Embedding model to use (default: text-embedding-ada-002)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            chunk = DocumentChunkSelector.get_by_id(chunk_id)
            if not chunk:
                logger.error(f"Document chunk {chunk_id} not found for re-embedding")
                return False
            
            # Import embedding service
            from ai_decisions.services.embedding_service import EmbeddingService
            
            # Generate new embedding
            embedding = EmbeddingService.generate_embedding(chunk.chunk_text, model=model)
            if not embedding or len(embedding) != 1536:
                logger.error(f"Failed to generate valid embedding for chunk {chunk_id}")
                return False
            
            # Update chunk with new embedding
            DocumentChunkRepository.update_embedding(chunk, embedding, version=getattr(chunk, "version", None))
            
            logger.info(f"Successfully regenerated embedding for chunk {chunk_id} using model {model}")
            return True
            
        except Exception as e:
            logger.error(f"Error regenerating embedding for chunk {chunk_id}: {e}", exc_info=True)
            return False