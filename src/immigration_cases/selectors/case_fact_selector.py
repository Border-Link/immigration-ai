from immigration_cases.models.case_fact import CaseFact
from immigration_cases.models.case import Case


class CaseFactSelector:
    """Selector for CaseFact read operations."""

    @staticmethod
    def get_all(use_cache: bool = False):
        """Get all case facts."""
        queryset = CaseFact.objects.select_related('case', 'case__user').all().order_by('-created_at')
        return queryset

    @staticmethod
    def get_by_case(case: Case, use_cache: bool = True):
        """Get facts by case."""
        queryset = CaseFact.objects.select_related('case', 'case__user').filter(
            case=case
        ).order_by('-created_at')
        return queryset

    @staticmethod
    def get_by_fact_key(case: Case, fact_key: str):
        """Get facts by case and fact key."""
        return CaseFact.objects.select_related('case', 'case__user').filter(
            case=case,
            fact_key=fact_key
        ).order_by('-created_at')

    @staticmethod
    def get_latest_by_fact_key(case: Case, fact_key: str):
        """Get latest fact by case and fact key."""
        return CaseFact.objects.select_related('case', 'case__user').filter(
            case=case,
            fact_key=fact_key
        ).order_by('-created_at').first()

    @staticmethod
    def get_by_source(source: str):
        """Get facts by source."""
        return CaseFact.objects.select_related('case', 'case__user').filter(
            source=source
        ).order_by('-created_at')

    @staticmethod
    def get_by_id(fact_id):
        """Get case fact by ID."""
        return CaseFact.objects.select_related('case', 'case__user').get(id=fact_id)

    @staticmethod
    def get_by_filters(case_id=None, fact_key=None, source=None, date_from=None, date_to=None):
        """Get case facts with advanced filtering for admin."""
        queryset = CaseFact.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).all()
        
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        
        if fact_key:
            queryset = queryset.filter(fact_key=fact_key)
        
        if source:
            queryset = queryset.filter(source=source)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_none():
        """Return an empty queryset."""
        return CaseFact.objects.none()
