from compliance.models.audit_log import AuditLog


class AuditLogSelector:
    """Selector for AuditLog read operations."""

    @staticmethod
    def get_all():
        """Get all audit logs."""
        return AuditLog.objects.filter(is_deleted=False).order_by('-timestamp')

    @staticmethod
    def get_by_level(level: str):
        """Get audit logs by level."""
        return AuditLog.objects.filter(level=level, is_deleted=False).order_by('-timestamp')

    @staticmethod
    def get_by_logger_name(logger_name: str):
        """Get audit logs by logger name."""
        return AuditLog.objects.filter(logger_name=logger_name, is_deleted=False).order_by('-timestamp')

    @staticmethod
    def get_by_id(log_id):
        """Get audit log by ID."""
        return AuditLog.objects.filter(id=log_id, is_deleted=False).first()

    @staticmethod
    def get_recent(limit: int = 100):
        """Get recent audit logs."""
        return AuditLog.objects.filter(is_deleted=False).order_by('-timestamp')[:limit]

    @staticmethod
    def get_by_date_range(start_date=None, end_date=None):
        """
        Get audit logs within a date range.

        Supports open-ended ranges:
        - start_date only: all logs from start_date onwards
        - end_date only: all logs up to end_date
        - neither: all logs
        """
        qs = AuditLog.objects.filter(is_deleted=False)
        if start_date is not None:
            qs = qs.filter(timestamp__gte=start_date)
        if end_date is not None:
            qs = qs.filter(timestamp__lte=end_date)
        return qs.order_by('-timestamp')

