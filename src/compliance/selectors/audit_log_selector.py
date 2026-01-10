from compliance.models.audit_log import AuditLog


class AuditLogSelector:
    """Selector for AuditLog read operations."""

    @staticmethod
    def get_all():
        """Get all audit logs."""
        return AuditLog.objects.all().order_by('-timestamp')

    @staticmethod
    def get_by_level(level: str):
        """Get audit logs by level."""
        return AuditLog.objects.filter(level=level).order_by('-timestamp')

    @staticmethod
    def get_by_logger_name(logger_name: str):
        """Get audit logs by logger name."""
        return AuditLog.objects.filter(logger_name=logger_name).order_by('-timestamp')

    @staticmethod
    def get_by_id(log_id):
        """Get audit log by ID."""
        return AuditLog.objects.get(id=log_id)

    @staticmethod
    def get_recent(limit: int = 100):
        """Get recent audit logs."""
        return AuditLog.objects.all().order_by('-timestamp')[:limit]

    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Get audit logs within a date range."""
        return AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('-timestamp')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return AuditLog.objects.none()

    @staticmethod
    def get_by_filters(level: str = None, logger_name: str = None, date_from=None, date_to=None, limit: int = None):
        """Get audit logs with filters."""
        queryset = AuditLog.objects.all()
        
        if level:
            queryset = queryset.filter(level=level)
        if logger_name:
            queryset = queryset.filter(logger_name=logger_name)
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        queryset = queryset.order_by('-timestamp')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get audit log statistics."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = AuditLog.objects.all()
        
        total_logs = queryset.count()
        logs_by_level = queryset.values('level').annotate(
            count=Count('id')
        ).order_by('-count')
        logs_by_logger = queryset.values('logger_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 loggers
        
        # Recent activity (last 24 hours, 7 days, 30 days)
        now = timezone.now()
        last_24h = queryset.filter(timestamp__gte=now - timedelta(hours=24)).count()
        last_7d = queryset.filter(timestamp__gte=now - timedelta(days=7)).count()
        last_30d = queryset.filter(timestamp__gte=now - timedelta(days=30)).count()
        
        # Error logs (ERROR, CRITICAL levels)
        error_logs = queryset.filter(level__in=['ERROR', 'CRITICAL']).count()
        
        return {
            'total': total_logs,
            'error_logs': error_logs,
            'by_level': list(logs_by_level),
            'top_loggers': list(logs_by_logger),
            'recent_activity': {
                'last_24_hours': last_24h,
                'last_7_days': last_7d,
                'last_30_days': last_30d,
            },
        }
