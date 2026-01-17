from data_ingestion.models.document_chunk import DocumentChunk


class DocumentChunkSelector:
    """Selector for DocumentChunk read operations."""

    @staticmethod
    def get_all():
        """Get all document chunks."""
        return DocumentChunk.objects.select_related('document_version').filter(is_deleted=False)

    @staticmethod
    def get_by_document_version(document_version_id: str):
        """Get document chunks by document version ID."""
        return DocumentChunk.objects.select_related('document_version').filter(
            document_version_id=document_version_id,
            is_deleted=False,
        ).order_by('chunk_index')

    @staticmethod
    def get_by_id(chunk_id):
        """Get document chunk by ID."""
        return DocumentChunk.objects.select_related('document_version').filter(id=chunk_id, is_deleted=False).first()

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return DocumentChunk.objects.none()

    @staticmethod
    def get_by_filters(document_version_id: str = None, has_embedding: bool = None):
        """Get document chunks with filters."""
        if document_version_id:
            queryset = DocumentChunkSelector.get_by_document_version(document_version_id)
        else:
            queryset = DocumentChunkSelector.get_all()
        
        if has_embedding is not None:
            if has_embedding:
                queryset = queryset.exclude(embedding__isnull=True)
            else:
                queryset = queryset.filter(embedding__isnull=True)
        
        queryset = queryset.order_by('document_version', 'chunk_index')
        return queryset

    @staticmethod
    def get_statistics():
        """Get document chunk statistics."""
        queryset = DocumentChunk.objects.filter(is_deleted=False)
        
        total_chunks = queryset.count()
        chunks_with_embeddings = queryset.exclude(embedding__isnull=True).count()
        chunks_without_embeddings = queryset.filter(embedding__isnull=True).count()
        
        return {
            'total': total_chunks,
            'with_embeddings': chunks_with_embeddings,
            'without_embeddings': chunks_without_embeddings,
            'embedding_coverage': round((chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0, 2),
        }
