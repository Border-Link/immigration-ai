"""
Admin API Views for AI Decisions Analytics and Statistics

Admin-only endpoints for AI decisions analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.services.ai_reasoning_log_service import AIReasoningLogService
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.serializers.ai_decisions_analytics import (
    TokenUsageAnalyticsQuerySerializer,
    CitationQualityAnalyticsQuerySerializer
)

logger = logging.getLogger('django')


class AIDecisionsStatisticsAPI(AuthAPI):
    """
    Admin: Get AI decisions statistics and analytics.
    
    Endpoint: GET /api/v1/ai-decisions/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        eligibility_stats = EligibilityResultService.get_statistics()
        reasoning_stats = AIReasoningLogService.get_statistics()
        citation_stats = AICitationService.get_statistics()
        
        statistics = {
            'eligibility_results': eligibility_stats,
            'ai_reasoning_logs': reasoning_stats,
            'ai_citations': citation_stats,
        }
        
        return self.api_response(
            message="AI decisions statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )


class TokenUsageAnalyticsAPI(AuthAPI):
    """
    Admin: Get token usage analytics for cost tracking.
    
    Endpoint: GET /api/v1/ai-decisions/admin/token-usage/
    Auth: Required (staff/superuser only)
    Query Params:
        - model_name: Filter by model name
        - date_from: Filter by date (from)
        - date_to: Filter by date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = TokenUsageAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        from django.db.models import Count, Sum, Avg
        
        logs = AIReasoningLogService.get_by_filters(
            model_name=validated_params.get('model_name'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        avg_tokens = logs.aggregate(avg=Avg('tokens_used'))['avg'] or 0.0
        count = logs.count()
        
        # Group by model
        by_model = logs.values('model_name').annotate(
            count=Count('id'),
            total_tokens=Sum('tokens_used'),
            avg_tokens=Avg('tokens_used')
        ).order_by('-total_tokens')
        
        analytics = {
            'total_tokens': total_tokens,
            'average_tokens_per_log': round(avg_tokens, 2),
            'total_logs': count,
            'by_model': list(by_model),
        }
        
        return self.api_response(
            message="Token usage analytics retrieved successfully.",
            data=analytics,
            status_code=status.HTTP_200_OK
        )


class CitationQualityAnalyticsAPI(AuthAPI):
    """
    Admin: Get citation quality analytics.
    
    Endpoint: GET /api/v1/ai-decisions/admin/citation-quality/
    Auth: Required (staff/superuser only)
    Query Params:
        - min_relevance: Filter by minimum relevance score
        - date_from: Filter by date (from)
        - date_to: Filter by date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CitationQualityAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        from django.db.models import Count, Avg
        
        citations = AICitationService.get_by_filters(
            min_relevance=validated_params.get('min_relevance'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        total_citations = citations.count()
        avg_relevance = citations.aggregate(avg=Avg('relevance_score'))['avg'] or 0.0
        
        # Quality distribution
        quality_distribution = {
            'high_quality': citations.filter(relevance_score__gte=0.8).count(),
            'medium_quality': citations.filter(
                relevance_score__gte=0.5,
                relevance_score__lt=0.8
            ).count(),
            'low_quality': citations.filter(relevance_score__lt=0.5).count(),
        }
        
        # Citations per reasoning log
        citations_per_log = citations.values('reasoning_log').annotate(
            count=Count('id')
        ).aggregate(avg=Avg('count'))['avg'] or 0.0
        
        analytics = {
            'total_citations': total_citations,
            'average_relevance_score': round(avg_relevance, 3),
            'quality_distribution': quality_distribution,
            'average_citations_per_log': round(citations_per_log, 2),
        }
        
        return self.api_response(
            message="Citation quality analytics retrieved successfully.",
            data=analytics,
            status_code=status.HTTP_200_OK
        )
