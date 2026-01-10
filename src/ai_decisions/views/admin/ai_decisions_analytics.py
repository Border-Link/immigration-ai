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

logger = logging.getLogger('django')


class AIDecisionsStatisticsAPI(AuthAPI):
    """
    Admin: Get AI decisions statistics and analytics.
    
    Endpoint: GET /api/v1/ai-decisions/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving AI decisions statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving AI decisions statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        model_name = request.query_params.get('model_name', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            from django.utils.dateparse import parse_datetime
            from django.db.models import Count, Sum, Avg
            
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            logs = AIReasoningLogService.get_by_filters(
                model_name=model_name,
                date_from=parsed_date_from,
                date_to=parsed_date_to
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
        except Exception as e:
            logger.error(f"Error retrieving token usage analytics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving token usage analytics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        min_relevance = request.query_params.get('min_relevance', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            from django.utils.dateparse import parse_datetime
            from django.db.models import Count, Avg
            
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            min_relevance_float = float(min_relevance) if min_relevance else None
            
            citations = AICitationService.get_by_filters(
                min_relevance=min_relevance_float,
                date_from=parsed_date_from,
                date_to=parsed_date_to
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
        except Exception as e:
            logger.error(f"Error retrieving citation quality analytics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving citation quality analytics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
