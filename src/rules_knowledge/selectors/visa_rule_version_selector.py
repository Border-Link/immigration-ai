from django.utils import timezone
from django.db import models
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.visa_type import VisaType


class VisaRuleVersionSelector:
    """Selector for VisaRuleVersion read operations."""

    @staticmethod
    def get_all():
        """Get all rule versions (excluding soft-deleted)."""
        return VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version',
            'source_document_version__source_document'
        ).filter(is_deleted=False).order_by('-effective_from')

    @staticmethod
    def get_by_visa_type(visa_type: VisaType):
        """Get rule versions by visa type (excluding soft-deleted)."""
        return VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version',
            'source_document_version__source_document'
        ).filter(visa_type=visa_type, is_deleted=False).order_by('-effective_from')

    @staticmethod
    def get_current_by_visa_type(visa_type: VisaType, use_cache: bool = True):
        """Get current rule version for a visa type (excluding soft-deleted, with caching)."""
        from django.core.cache import cache
        
        cache_key = f"current_rule_version:{visa_type.id}"
        
        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        now = timezone.now()
        version = VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version',
            'source_document_version__source_document'
        ).filter(
            visa_type=visa_type,
            effective_from__lte=now,
            is_published=True,
            is_deleted=False
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=now)
        ).order_by('-effective_from').first()
        
        if use_cache and version:
            cache.set(cache_key, version, timeout=3600)  # 1 hour cache
        
        return version

    @staticmethod
    def get_published():
        """Get all published rule versions (excluding soft-deleted)."""
        return VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version',
            'source_document_version__source_document'
        ).filter(is_published=True, is_deleted=False).order_by('-effective_from')

    @staticmethod
    def get_by_id(version_id, include_deleted: bool = False):
        """Get rule version by ID."""
        queryset = VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version',
            'source_document_version__source_document'
        )
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        return queryset.get(id=version_id)

    @staticmethod
    def get_by_filters(visa_type_id=None, is_published=None, jurisdiction=None, date_from=None, date_to=None, effective_from=None, effective_to=None, include_deleted: bool = False):
        """Get rule versions with advanced filtering for admin."""
        queryset = VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version',
            'source_document_version__source_document'
        )
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        if visa_type_id:
            queryset = queryset.filter(visa_type_id=visa_type_id)
        
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published)
        
        if jurisdiction:
            queryset = queryset.filter(visa_type__jurisdiction=jurisdiction)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if effective_from:
            queryset = queryset.filter(effective_from__gte=effective_from)
        
        if effective_to:
            queryset = queryset.filter(effective_to__lte=effective_to)
        
        return queryset.order_by('-effective_from')
