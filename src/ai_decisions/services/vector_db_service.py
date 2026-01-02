import logging
from typing import List, Dict, Optional
from django.db.models import Q
from pgvector.django import CosineDistance
from data_ingestion.models.document_chunk import DocumentChunk
from data_ingestion.models.document_version import DocumentVersion

logger = logging.getLogger('django')


class VectorDBService:
    """
    Service for vector similarity search using pgvector.
    Handles storing and querying document chunks with embeddings.
    """

    @staticmethod
    def store_chunks(
        document_version: DocumentVersion,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> List[DocumentChunk]:
        """
        Store document chunks with embeddings.
        
        Args:
            document_version: DocumentVersion instance
            chunks: List of dicts with 'text' and 'metadata'
            embeddings: List of embedding vectors (1536 dims for ada-002)
            
        Returns:
            List of created DocumentChunk objects
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")
        
        try:
            chunk_objects = []
            for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                # Validate embedding dimensions
                if len(embedding) != 1536:
                    logger.warning(
                        f"Skipping chunk {i}: embedding has {len(embedding)} dimensions, expected 1536"
                    )
                    continue
                
                chunk = DocumentChunk.objects.create(
                    document_version=document_version,
                    chunk_text=chunk_data.get('text', ''),
                    chunk_index=chunk_data.get('metadata', {}).get('chunk_index', i),
                    embedding=embedding,
                    metadata=chunk_data.get('metadata', {})
                )
                chunk_objects.append(chunk)
            
            logger.info(
                f"Stored {len(chunk_objects)} chunks for document version {document_version.id}"
            )
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Error storing chunks: {e}", exc_info=True)
            raise

    @staticmethod
    def search_similar(
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
        similarity_threshold: float = 0.7,
        document_version_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: Query vector (1536 dims)
            limit: Maximum number of results
            filters: Optional metadata filters (e.g., {'visa_code': 'SKILLED_WORKER'})
            similarity_threshold: Minimum similarity score (0-1, where 1 is identical)
            document_version_id: Optional filter by specific document version
            
        Returns:
            List of DocumentChunk objects ordered by similarity (most similar first)
        """
        if not query_embedding:
            return []
        
        if len(query_embedding) != 1536:
            logger.error(f"Query embedding has {len(query_embedding)} dimensions, expected 1536")
            return []
        
        try:
            # Start with base query
            queryset = DocumentChunk.objects.filter(
                embedding__isnull=False
            )
            
            # Filter by document version if specified
            if document_version_id:
                queryset = queryset.filter(document_version_id=document_version_id)
            
            # Apply metadata filters
            if filters:
                for key, value in filters.items():
                    # Use JSON field contains lookup
                    queryset = queryset.filter(metadata__contains={key: value})
            
            # Vector similarity search using cosine distance
            # Lower distance = higher similarity
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            queryset = queryset.annotate(
                distance=CosineDistance('embedding', query_embedding)
            ).order_by('distance')
            
            # Filter by similarity threshold
            # Cosine distance: 0 = identical, 2 = opposite
            # Similarity = 1 - (distance / 2)
            # So distance <= 0.6 means similarity >= 0.7
            max_distance = 2 * (1 - similarity_threshold)
            queryset = queryset.filter(distance__lte=max_distance)
            
            # Limit results
            results = list(queryset[:limit])
            
            logger.info(
                f"Found {len(results)} similar chunks "
                f"(threshold: {similarity_threshold}, limit: {limit})"
            )
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}", exc_info=True)
            return []

    @staticmethod
    def get_chunks_by_document_version(
        document_version: DocumentVersion
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a document version.
        
        Args:
            document_version: DocumentVersion instance
            
        Returns:
            List of DocumentChunk objects ordered by chunk_index
        """
        return list(
            DocumentChunk.objects.filter(
                document_version=document_version
            ).order_by('chunk_index')
        )

    @staticmethod
    def delete_chunks_by_document_version(document_version: DocumentVersion) -> int:
        """
        Delete all chunks for a document version.
        
        Args:
            document_version: DocumentVersion instance
            
        Returns:
            Number of deleted chunks
        """
        count, _ = DocumentChunk.objects.filter(
            document_version=document_version
        ).delete()
        
        logger.info(
            f"Deleted {count} chunks for document version {document_version.id}"
        )
        return count

    @staticmethod
    def update_chunks_for_document_version(
        document_version: DocumentVersion,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> List[DocumentChunk]:
        """
        Update chunks for a document version (delete old, create new).
        
        Args:
            document_version: DocumentVersion instance
            chunks: List of dicts with 'text' and 'metadata'
            embeddings: List of embedding vectors
            
        Returns:
            List of created DocumentChunk objects
        """
        # Delete existing chunks
        VectorDBService.delete_chunks_by_document_version(document_version)
        
        # Create new chunks
        return VectorDBService.store_chunks(document_version, chunks, embeddings)

