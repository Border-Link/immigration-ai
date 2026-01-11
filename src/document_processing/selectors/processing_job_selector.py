"""
Selector for ProcessingJob read operations.
"""
from document_processing.models.processing_job import ProcessingJob


class ProcessingJobSelector:
    """Selector for ProcessingJob read operations."""

    @staticmethod
    def get_all():
        """Get all processing jobs."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_id(job_id):
        """Get processing job by ID."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).get(id=job_id)

    @staticmethod
    def get_by_case_document(case_document_id: str):
        """Get processing jobs by case document."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).filter(case_document_id=case_document_id).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str):
        """Get processing jobs by status."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).filter(status=status).order_by('-created_at')

    @staticmethod
    def get_by_processing_type(processing_type: str):
        """Get processing jobs by processing type."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).filter(processing_type=processing_type).order_by('-created_at')

    @staticmethod
    def get_by_celery_task_id(celery_task_id: str):
        """Get processing job by Celery task ID."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).filter(celery_task_id=celery_task_id).first()

    @staticmethod
    def get_pending():
        """Get all pending processing jobs."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).filter(status='pending').order_by('-priority', 'created_at')

    @staticmethod
    def get_failed():
        """Get all failed processing jobs."""
        return ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).filter(status='failed').order_by('-created_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return ProcessingJob.objects.none()

    @staticmethod
    def get_by_filters(
        case_document_id: str = None,
        status: str = None,
        processing_type: str = None,
        error_type: str = None,
        created_by_id: str = None,
        date_from=None,
        date_to=None,
        min_priority: int = None,
        max_retries_exceeded: bool = None
    ):
        """Get processing jobs with filters."""
        queryset = ProcessingJob.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type',
            'created_by'
        ).all()
        
        if case_document_id:
            queryset = queryset.filter(case_document_id=case_document_id)
        if status:
            queryset = queryset.filter(status=status)
        if processing_type:
            queryset = queryset.filter(processing_type=processing_type)
        if error_type:
            queryset = queryset.filter(error_type=error_type)
        if created_by_id:
            queryset = queryset.filter(created_by_id=created_by_id)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        if min_priority is not None:
            queryset = queryset.filter(priority__gte=min_priority)
        if max_retries_exceeded is not None:
            from django.db.models import F
            if max_retries_exceeded:
                queryset = queryset.filter(retry_count__gte=F('max_retries'))
            else:
                queryset = queryset.filter(retry_count__lt=F('max_retries'))
        
        queryset = queryset.order_by('-priority', '-created_at')
        return queryset

    @staticmethod
    def get_statistics():
        """Get processing job statistics."""
        from django.db.models import Count, Avg, Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = ProcessingJob.objects.all()
        
        total_jobs = queryset.count()
        jobs_by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        jobs_by_type = queryset.values('processing_type').annotate(
            count=Count('id')
        ).order_by('processing_type')
        
        # Failed jobs
        failed_jobs = queryset.filter(status='failed').count()
        completed_jobs = queryset.filter(status='completed').count()
        pending_jobs = queryset.filter(status='pending').count()
        processing_jobs = queryset.filter(status='processing').count()
        
        # Average processing time
        completed_with_time = queryset.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        avg_processing_time = None
        if completed_with_time.exists():
            from django.db.models import F, ExpressionWrapper, DurationField
            time_diff = ExpressionWrapper(
                F('completed_at') - F('started_at'),
                output_field=DurationField()
            )
            avg_duration = completed_with_time.annotate(
                duration=time_diff
            ).aggregate(avg=Avg('duration'))['avg']
            if avg_duration:
                avg_processing_time = avg_duration.total_seconds() * 1000  # Convert to milliseconds
        
        # Recent activity
        now = timezone.now()
        last_24h = queryset.filter(created_at__gte=now - timedelta(hours=24)).count()
        last_7d = queryset.filter(created_at__gte=now - timedelta(days=7)).count()
        last_30d = queryset.filter(created_at__gte=now - timedelta(days=30)).count()
        
        # Jobs with errors
        jobs_with_errors = queryset.exclude(error_type__isnull=True).exclude(error_type='').count()
        
        # Retry statistics
        from django.db.models import F
        jobs_requiring_retry = queryset.filter(
            status='failed',
            retry_count__lt=F('max_retries')
        ).count()
        jobs_exceeded_retries = queryset.filter(
            retry_count__gte=F('max_retries')
        ).count()
        
        return {
            'total': total_jobs,
            'by_status': list(jobs_by_status),
            'by_type': list(jobs_by_type),
            'failed': failed_jobs,
            'completed': completed_jobs,
            'pending': pending_jobs,
            'processing': processing_jobs,
            'average_processing_time_ms': round(avg_processing_time, 2) if avg_processing_time else None,
            'with_errors': jobs_with_errors,
            'requiring_retry': jobs_requiring_retry,
            'exceeded_retries': jobs_exceeded_retries,
            'recent_activity': {
                'last_24_hours': last_24h,
                'last_7_days': last_7d,
                'last_30_days': last_30d,
            },
        }
