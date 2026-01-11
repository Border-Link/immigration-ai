from django.core.cache import cache
from django.utils import timezone
from immigration_cases.models.case import Case


class CaseSelector:
    """Selector for Case read operations."""

    @staticmethod
    def get_all(use_cache: bool = False):
        """Get all cases, excluding soft-deleted ones."""
        if use_cache:
            cache_key = "cases:all"
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        queryset = Case.objects.select_related('user', 'user__profile').filter(
            is_deleted=False
        ).order_by('-created_at')
        
        if use_cache:
            cache.set(cache_key, queryset, timeout=300)  # 5 minutes
        
        return queryset

    @staticmethod
    def get_by_user(user, use_cache: bool = True):
        """Get cases by user, excluding soft-deleted ones."""
        if use_cache:
            cache_key = f"cases:user:{user.id}"
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        queryset = Case.objects.select_related('user', 'user__profile').filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')
        
        if use_cache:
            cache.set(cache_key, queryset, timeout=600)  # 10 minutes
        
        return queryset

    @staticmethod
    def get_by_status(status: str):
        """Get cases by status, excluding soft-deleted ones."""
        return Case.objects.select_related('user', 'user__profile').filter(
            status=status,
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_by_jurisdiction(jurisdiction: str):
        """Get cases by jurisdiction, excluding soft-deleted ones."""
        return Case.objects.select_related('user', 'user__profile').filter(
            jurisdiction=jurisdiction,
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_by_id(case_id, use_cache: bool = True):
        """Get case by ID, excluding soft-deleted ones."""
        if use_cache:
            cache_key = f"case:{case_id}"
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        case = Case.objects.select_related('user', 'user__profile').filter(
            is_deleted=False
        ).get(id=case_id)
        
        if use_cache:
            cache.set(cache_key, case, timeout=3600)  # 1 hour cache
        
        return case

    @staticmethod
    def get_by_user_and_status(user, status: str):
        """Get cases by user and status, excluding soft-deleted ones."""
        return Case.objects.select_related('user', 'user__profile').filter(
            user=user,
            status=status,
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_by_filters(user_id=None, jurisdiction=None, status=None, date_from=None, date_to=None, updated_date_from=None, updated_date_to=None, include_deleted=False):
        """Get cases with advanced filtering for admin."""
        queryset = Case.objects.select_related(
            'user',
            'user__profile'
        ).all()
        
        # Filter soft-deleted by default unless explicitly requested
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if jurisdiction:
            queryset = queryset.filter(jurisdiction=jurisdiction)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if updated_date_from:
            queryset = queryset.filter(updated_at__gte=updated_date_from)
        
        if updated_date_to:
            queryset = queryset.filter(updated_at__lte=updated_date_to)
        
        return queryset.order_by('-created_at')
