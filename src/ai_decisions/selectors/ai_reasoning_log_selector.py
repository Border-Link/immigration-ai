from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from immigration_cases.models.case import Case


class AIReasoningLogSelector:
    """Selector for AIReasoningLog read operations."""

    @staticmethod
    def get_all():
        """Get all AI reasoning logs."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get reasoning logs by case."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(case=case, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_model(model_name: str):
        """Get reasoning logs by model name."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(model_name=model_name, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(log_id):
        """Get reasoning log by ID."""
        return AIReasoningLog.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).get(id=log_id, is_deleted=False)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return AIReasoningLog.objects.none()

    @staticmethod
    def get_statistics():
        """Get AI reasoning log statistics."""
        from django.db.models import Count, Sum, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = AIReasoningLog.objects.filter(is_deleted=False)
        
        total_logs = queryset.count()
        logs_by_model = queryset.values('model_name').annotate(
            count=Count('id'),
            total_tokens=Sum('tokens_used')
        ).order_by('-count')
        
        total_tokens = queryset.aggregate(
            total=Sum('tokens_used')
        )['total'] or 0
        
        avg_tokens_per_log = queryset.aggregate(
            avg=Avg('tokens_used')
        )['avg'] or 0.0
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_logs = queryset.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Cases with AI reasoning
        cases_with_ai_reasoning = queryset.values('case').distinct().count()
        
        return {
            'total': total_logs,
            'by_model': list(logs_by_model),
            'total_tokens': total_tokens,
            'average_tokens_per_log': round(avg_tokens_per_log, 2),
            'recent_30_days': recent_logs,
            'cases_with_ai_reasoning': cases_with_ai_reasoning,
        }
