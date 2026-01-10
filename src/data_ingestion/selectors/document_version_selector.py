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

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return DocumentVersion.objects.none()

    @staticmethod
    def get_by_filters(source_document=None, date_from=None, date_to=None):
        """Get document versions with filters."""
        if source_document:
            queryset = DocumentVersionSelector.get_by_source_document(source_document)
        else:
            queryset = DocumentVersionSelector.get_all()
        
        if date_from:
            queryset = queryset.filter(extracted_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(extracted_at__lte=date_to)
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get document version statistics."""
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = DocumentVersion.objects.all()
        
        total_versions = queryset.count()
        unique_hashes = queryset.values('content_hash').distinct().count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_versions = queryset.filter(
            extracted_at__gte=thirty_days_ago
        ).count()
        
        return {
            'total': total_versions,
            'unique_hashes': unique_hashes,
            'recent_30_days': recent_versions,
        }
