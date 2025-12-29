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

