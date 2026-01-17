"""
Selector for ProcessingHistory read operations.
"""
from document_processing.models.processing_history import ProcessingHistory


class ProcessingHistorySelector:
    """Selector for ProcessingHistory read operations."""

    @staticmethod
    def get_all():
        """Get all processing history entries."""
        return ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(history_id):
        """Get processing history entry by ID."""
        return ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(is_deleted=False).get(id=history_id)

    @staticmethod
    def get_by_case_document(case_document_id: str):
        """Get processing history by case document."""
        return ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(case_document_id=case_document_id, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_processing_job(processing_job_id: str):
        """Get processing history by processing job."""
        return ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(processing_job_id=processing_job_id, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_action(action: str):
        """Get processing history by action."""
        return ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(action=action, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str):
        """Get processing history by status."""
        return ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(status=status, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return ProcessingHistory.objects.none()

    @staticmethod
    def get_by_filters(
        case_document_id: str = None,
        processing_job_id: str = None,
        action: str = None,
        status: str = None,
        error_type: str = None,
        user_id: str = None,
        date_from=None,
        date_to=None,
        limit: int = None
    ):
        """Get processing history with filters."""
        queryset = ProcessingHistory.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'processing_job',
            'user'
        ).filter(is_deleted=False)
        
        if case_document_id:
            queryset = queryset.filter(case_document_id=case_document_id)
        if processing_job_id:
            queryset = queryset.filter(processing_job_id=processing_job_id)
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(status=status)
        if error_type:
            queryset = queryset.filter(error_type=error_type)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        queryset = queryset.order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get processing history statistics."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = ProcessingHistory.objects.filter(is_deleted=False)
        
        total_entries = queryset.count()
        entries_by_action = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('action')
        entries_by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Recent activity
        now = timezone.now()
        last_24h = queryset.filter(created_at__gte=now - timedelta(hours=24)).count()
        last_7d = queryset.filter(created_at__gte=now - timedelta(days=7)).count()
        last_30d = queryset.filter(created_at__gte=now - timedelta(days=30)).count()
        
        # Failed actions
        failed_actions = queryset.filter(status='failure').count()
        successful_actions = queryset.filter(status='success').count()
        warning_actions = queryset.filter(status='warning').count()
        
        # Actions with errors
        actions_with_errors = queryset.exclude(error_type__isnull=True).exclude(error_type='').count()
        
        # Average processing time
        from django.db.models import Avg
        avg_processing_time = queryset.exclude(processing_time_ms__isnull=True).aggregate(
            avg=Avg('processing_time_ms')
        )['avg'] or 0
        
        return {
            'total': total_entries,
            'by_action': list(entries_by_action),
            'by_status': list(entries_by_status),
            'failed': failed_actions,
            'successful': successful_actions,
            'warning': warning_actions,
            'with_errors': actions_with_errors,
            'average_processing_time_ms': round(avg_processing_time, 2),
            'recent_activity': {
                'last_24_hours': last_24h,
                'last_7_days': last_7d,
                'last_30_days': last_30d,
            },
        }
