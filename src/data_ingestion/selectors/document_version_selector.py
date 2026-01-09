from data_ingestion.models.document_version import DocumentVersion


class DocumentVersionSelector:
    """Selector for DocumentVersion read operations."""

    @staticmethod
    def get_all():
        """Get all document versions."""
        return DocumentVersion.objects.select_related('source_document', 'source_document__data_source').all()

    @staticmethod
    def get_by_source_document(source_document):
        """Get document versions by source document."""
        return DocumentVersion.objects.select_related(
            'source_document', 'source_document__data_source'
        ).filter(source_document=source_document).order_by('-extracted_at')

    @staticmethod
    def get_by_hash(content_hash: str):
        """Get document version by content hash."""
        return DocumentVersion.objects.select_related(
            'source_document', 'source_document__data_source'
        ).filter(content_hash=content_hash).first()

    @staticmethod
    def get_latest_by_source_document(source_document):
        """Get latest document version for a source document."""
        return DocumentVersion.objects.select_related(
            'source_document', 'source_document__data_source'
        ).filter(source_document=source_document).order_by('-extracted_at').first()

    @staticmethod
    def get_by_id(version_id):
        """Get document version by ID."""
        return DocumentVersion.objects.select_related(
            'source_document', 'source_document__data_source'
        ).get(id=version_id)
    
    @staticmethod
    def get_by_jurisdiction(jurisdiction: str):
        """Get document versions by jurisdiction."""
        return DocumentVersion.objects.select_related(
            'source_document', 'source_document__data_source'
        ).filter(
            source_document__data_source__jurisdiction=jurisdiction
        ).order_by('-extracted_at')

