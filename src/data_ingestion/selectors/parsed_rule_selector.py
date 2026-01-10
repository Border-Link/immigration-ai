from data_ingestion.models.parsed_rule import ParsedRule


class ParsedRuleSelector:
    """Selector for ParsedRule read operations."""

    @staticmethod
    def get_all():
        """Get all parsed rules."""
        return ParsedRule.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source'
        ).all()

    @staticmethod
    def get_by_status(status: str):
        """Get parsed rules by status."""
        return ParsedRule.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source'
        ).filter(status=status).order_by('-created_at')

    @staticmethod
    def get_by_visa_code(visa_code: str):
        """Get parsed rules by visa code."""
        return ParsedRule.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source'
        ).filter(visa_code=visa_code).order_by('-created_at')

    @staticmethod
    def get_by_document_version(document_version):
        """Get parsed rules by document version."""
        return ParsedRule.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source'
        ).filter(document_version=document_version).order_by('-created_at')

    @staticmethod
    def get_pending():
        """Get all pending parsed rules."""
        return ParsedRule.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source'
        ).filter(status='pending').order_by('-confidence_score', '-created_at')

    @staticmethod
    def get_by_id(rule_id):
        """Get parsed rule by ID."""
        return ParsedRule.objects.select_related(
            'document_version',
            'document_version__source_document',
            'document_version__source_document__data_source'
        ).get(id=rule_id)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return ParsedRule.objects.none()

    @staticmethod
    def get_by_filters(status: str = None, visa_code: str = None, rule_type: str = None, min_confidence: float = None, date_from=None, date_to=None):
        """Get parsed rules with filters."""
        if status:
            queryset = ParsedRuleSelector.get_by_status(status)
        elif visa_code:
            queryset = ParsedRuleSelector.get_by_visa_code(visa_code)
        else:
            queryset = ParsedRuleSelector.get_all()
        
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        if min_confidence is not None:
            queryset = queryset.filter(confidence_score__gte=min_confidence)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get parsed rule statistics."""
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = ParsedRule.objects.all()
        
        total_rules = queryset.count()
        rules_by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        rules_by_type = queryset.values('rule_type').annotate(
            count=Count('id')
        ).order_by('-count')
        avg_confidence = queryset.aggregate(
            avg=Avg('confidence_score')
        )['avg'] or 0.0
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_rules = queryset.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        return {
            'total': total_rules,
            'by_status': list(rules_by_status),
            'by_type': list(rules_by_type),
            'average_confidence': round(avg_confidence, 3),
            'recent_30_days': recent_rules,
        }
