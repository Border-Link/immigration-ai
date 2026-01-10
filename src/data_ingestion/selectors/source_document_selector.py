from data_ingestion.models.source_document import SourceDocument


class SourceDocumentSelector:
    """Selector for SourceDocument read operations."""

    @staticmethod
    def get_all():
        """Get all source documents."""
        return SourceDocument.objects.select_related('data_source').all()

    @staticmethod
    def get_by_data_source(data_source):
        """Get source documents by data source."""
        return SourceDocument.objects.select_related('data_source').filter(
            data_source=data_source
        ).order_by('-fetched_at')

    @staticmethod
    def get_by_url(source_url: str):
        """Get source document by URL."""
        return SourceDocument.objects.select_related('data_source').filter(
            source_url=source_url
        ).order_by('-fetched_at').first()

    @staticmethod
    def get_latest_by_data_source(data_source):
        """Get latest source document for a data source."""
        return SourceDocument.objects.select_related('data_source').filter(
            data_source=data_source
        ).order_by('-fetched_at').first()

    @staticmethod
    def get_by_id(document_id):
        """Get source document by ID."""
        return SourceDocument.objects.select_related('data_source').get(id=document_id)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return SourceDocument.objects.none()

    @staticmethod
    def get_by_filters(data_source=None, has_error: bool = None, http_status: int = None, date_from=None, date_to=None):
        """Get source documents with filters."""
        from django.db.models import Q
        
        if data_source:
            queryset = SourceDocumentSelector.get_by_data_source(data_source)
        else:
            queryset = SourceDocumentSelector.get_all()
        
        if has_error is not None:
            if has_error:
                queryset = queryset.exclude(fetch_error__isnull=True).exclude(fetch_error='')
            else:
                queryset = queryset.filter(Q(fetch_error__isnull=True) | Q(fetch_error=''))
        if http_status:
            queryset = queryset.filter(http_status_code=http_status)
        if date_from:
            queryset = queryset.filter(fetched_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(fetched_at__lte=date_to)
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get source document statistics."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = SourceDocument.objects.all()
        
        total_documents = queryset.count()
        documents_with_errors = queryset.exclude(
            fetch_error__isnull=True
        ).exclude(fetch_error='').count()
        documents_by_status = queryset.values('http_status_code').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_documents = queryset.filter(
            fetched_at__gte=thirty_days_ago
        ).count()
        
        return {
            'total': total_documents,
            'with_errors': documents_with_errors,
            'successful': total_documents - documents_with_errors,
            'by_status_code': list(documents_by_status),
            'recent_30_days': recent_documents,
        }
