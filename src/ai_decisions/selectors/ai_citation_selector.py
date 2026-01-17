from ai_decisions.models.ai_citation import AICitation
from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from data_ingestion.models.document_version import DocumentVersion


class AICitationSelector:
    """Selector for AICitation read operations."""

    @staticmethod
    def get_all():
        """Get all AI citations."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_reasoning_log(reasoning_log: AIReasoningLog):
        """Get citations by reasoning log."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).filter(reasoning_log=reasoning_log, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_document_version(document_version: DocumentVersion):
        """Get citations by document version."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).filter(document_version=document_version, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(citation_id):
        """Get citation by ID."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).get(id=citation_id, is_deleted=False)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return AICitation.objects.none()

    @staticmethod
    def get_statistics():
        """Get AI citation statistics."""
        from django.db.models import Avg
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = AICitation.objects.filter(is_deleted=False)
        
        total_citations = queryset.count()
        avg_relevance_score = queryset.aggregate(
            avg=Avg('relevance_score')
        )['avg'] or 0.0
        
        citations_by_relevance_range = {
            'high': queryset.filter(relevance_score__gte=0.8).count(),
            'medium': queryset.filter(
                relevance_score__gte=0.5,
                relevance_score__lt=0.8
            ).count(),
            'low': queryset.filter(relevance_score__lt=0.5).count(),
        }
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_citations = queryset.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        return {
            'total': total_citations,
            'average_relevance_score': round(avg_relevance_score, 3),
            'by_relevance_range': citations_by_relevance_range,
            'recent_30_days': recent_citations,
        }
