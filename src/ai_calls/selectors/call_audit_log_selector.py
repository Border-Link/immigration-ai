from ai_calls.models.call_audit_log import CallAuditLog


class CallAuditLogSelector:
    """Selector for CallAuditLog read operations."""

    @staticmethod
    def get_all():
        """Get all audit logs."""
        return CallAuditLog.objects.select_related('call_session').filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_call_session(call_session):
        """Get audit logs for call session."""
        return CallAuditLog.objects.filter(
            call_session=call_session,
            is_deleted=False,
        ).order_by('-created_at')

    @staticmethod
    def get_by_id(audit_log_id):
        """Get audit log by ID."""
        return CallAuditLog.objects.select_related('call_session').filter(id=audit_log_id, is_deleted=False).first()

    @staticmethod
    def get_by_event_type(event_type: str):
        """Get audit logs by event type."""
        return CallAuditLog.objects.select_related('call_session').filter(
            event_type=event_type,
            is_deleted=False,
        ).order_by('-created_at')

    @staticmethod
    def get_by_filters(call_session_id=None, event_type=None, date_from=None, date_to=None):
        """Get audit logs with advanced filtering for admin."""
        queryset = CallAuditLog.objects.select_related('call_session').filter(is_deleted=False)
        
        if call_session_id:
            queryset = queryset.filter(call_session_id=call_session_id)
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return CallAuditLog.objects.none()
