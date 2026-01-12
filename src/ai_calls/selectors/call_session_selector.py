from django.core.cache import cache
from ai_calls.models.call_session import CallSession


class CallSessionSelector:
    """Selector for CallSession read operations."""

    @staticmethod
    def get_by_id(session_id, use_cache: bool = True):
        """Get call session by ID, excluding soft-deleted ones."""
        if use_cache:
            cache_key = f"call_session:{session_id}"
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        call_session = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            is_deleted=False
        ).get(id=session_id)
        
        if use_cache:
            cache.set(cache_key, call_session, timeout=300)  # 5 minutes
        
        return call_session

    @staticmethod
    def get_by_case(case, use_cache: bool = True):
        """Get all call sessions for a case, excluding soft-deleted ones."""
        if use_cache:
            cache_key = f"call_sessions:case:{case.id}"
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        queryset = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            case=case,
            is_deleted=False
        ).order_by('-created_at')
        
        if use_cache:
            cache.set(cache_key, queryset, timeout=300)  # 5 minutes
        
        return queryset

    @staticmethod
    def get_active_call_for_case(case, use_cache: bool = True):
        """Get active call session for a case (if exists)."""
        if use_cache:
            cache_key = f"call_session:case:{case.id}:active"
            cached = cache.get(cache_key)
            if cached is not None:  # None is a valid cached value
                return cached
        
        call_session = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            case=case,
            status__in=['created', 'ready', 'in_progress'],
            is_deleted=False
        ).order_by('-created_at').first()
        
        if use_cache:
            cache.set(cache_key, call_session, timeout=60)  # 1 minute (active calls change frequently)
        
        return call_session

    @staticmethod
    def get_by_user(user, use_cache: bool = True):
        """Get call sessions by user, excluding soft-deleted ones."""
        if use_cache:
            cache_key = f"call_sessions:user:{user.id}"
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        queryset = CallSession.objects.select_related(
            'case', 'user', 'summary'
        ).filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')
        
        if use_cache:
            cache.set(cache_key, queryset, timeout=300)  # 5 minutes
        
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
