from ai_calls.models.call_session import CallSession


class CallSessionSelector:
    """Selector for CallSession read operations."""

    @staticmethod
    def get_by_id(session_id, use_cache: bool = True, include_deleted: bool = False):
        """
        Get call session by ID.

        Returns None if not found (do not raise DoesNotExist) to keep view/service
        layers deterministic and avoid leaking 500s for simple not-found cases.
        """
        queryset = CallSession.objects.select_related('case', 'user', 'summary', 'parent_session').all()
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        return queryset.filter(id=session_id).first()

    @staticmethod
    def get_by_case(case, use_cache: bool = True):
        """Get all call sessions for a case, excluding soft-deleted ones."""
        queryset = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            case=case,
            is_deleted=False
        ).order_by('-created_at')
        return queryset

    @staticmethod
    def get_active_call_for_case(case, use_cache: bool = True):
        """Get active call session for a case (if exists)."""
        call_session = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            case=case,
            status__in=['created', 'ready', 'in_progress'],
            is_deleted=False
        ).order_by('-created_at').first()
        return call_session

    @staticmethod
    def get_by_user(user, use_cache: bool = True):
        """Get call sessions by user, excluding soft-deleted ones."""
        queryset = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')
        return queryset

    @staticmethod
    def get_by_status(status: str):
        """Get call sessions by status, excluding soft-deleted ones."""
        return CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            status=status,
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_by_filters(case_id=None, user_id=None, status=None, date_from=None, date_to=None, include_deleted=False):
        """Get call sessions with advanced filtering for admin."""
        queryset = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).all()
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_all(include_deleted: bool = False):
        """Get all call sessions, optionally including soft-deleted ones."""
        queryset = CallSession.objects.select_related(
            'case', 'user', 'summary', 'parent_session'
        ).all()
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return CallSession.objects.none()
