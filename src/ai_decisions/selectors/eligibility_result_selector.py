from ai_decisions.models.eligibility_result import EligibilityResult
from immigration_cases.models.case import Case
from rules_knowledge.models.visa_type import VisaType


class EligibilityResultSelector:
    """Selector for EligibilityResult read operations."""

    @staticmethod
    def get_all():
        """Get all eligibility results."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get eligibility results by case."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_visa_type(visa_type: VisaType):
        """Get eligibility results by visa type."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).filter(visa_type=visa_type).order_by('-created_at')

    @staticmethod
    def get_by_id(result_id):
        """Get eligibility result by ID."""
        return EligibilityResult.objects.select_related(
            'case',
            'case__user',
            'visa_type',
            'rule_version',
            'rule_version__visa_type'
        ).get(id=result_id)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return EligibilityResult.objects.none()

    @staticmethod
    def get_statistics():
        """Get eligibility result statistics."""
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = EligibilityResult.objects.all()
        
        total_results = queryset.count()
        results_by_outcome = queryset.values('outcome').annotate(
            count=Count('id')
        ).order_by('outcome')
        
        avg_confidence = queryset.aggregate(
            avg_confidence=Avg('confidence')
        )['avg_confidence'] or 0.0
        
        results_requiring_review = queryset.filter(
            outcome='requires_review'
        ).count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_results = queryset.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        return {
            'total': total_results,
            'by_outcome': list(results_by_outcome),
            'average_confidence': round(avg_confidence, 3),
            'requiring_review': results_requiring_review,
            'recent_30_days': recent_results,
        }
