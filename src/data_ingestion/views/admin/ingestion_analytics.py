"""
Admin API Views for Data Ingestion Analytics and Statistics

Admin-only endpoints for ingestion analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.services.source_document_service import SourceDocumentService
from data_ingestion.services.document_version_service import DocumentVersionService
from data_ingestion.services.document_chunk_service import DocumentChunkService
from data_ingestion.services.parsed_rule_service import ParsedRuleService
from data_ingestion.services.rule_validation_task_service import RuleValidationTaskService
from data_ingestion.services.audit_log_service import RuleParsingAuditLogService
from data_ingestion.serializers.ingestion_analytics.admin import ParsingCostAnalyticsQuerySerializer
from django.db.models import Count, Avg, Sum


class IngestionStatisticsAPI(AuthAPI):
    """
    Admin: Get data ingestion statistics and analytics.
    
    Endpoint: GET /api/v1/data-ingestion/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        data_source_stats = DataSourceService.get_statistics()
        source_document_stats = SourceDocumentService.get_statistics()
        document_version_stats = DocumentVersionService.get_statistics()
        document_chunk_stats = DocumentChunkService.get_statistics()
        parsed_rule_stats = ParsedRuleService.get_statistics()
        validation_task_stats = RuleValidationTaskService.get_statistics()
        audit_log_stats = RuleParsingAuditLogService.get_statistics()
        
        statistics = {
            'data_sources': data_source_stats,
            'source_documents': source_document_stats,
            'document_versions': document_version_stats,
            'document_chunks': document_chunk_stats,
            'parsed_rules': parsed_rule_stats,
            'validation_tasks': validation_task_stats,
            'audit_logs': audit_log_stats,
        }
        
        return self.api_response(
            message="Ingestion statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )


class ParsingCostAnalyticsAPI(AuthAPI):
    """
    Admin: Get parsing cost analytics for cost tracking.
    
    Endpoint: GET /api/v1/data-ingestion/admin/cost-analytics/
    Auth: Required (staff/superuser only)
    Query Params:
        - date_from: Filter by date (from)
        - date_to: Filter by date (to)
        - llm_model: Filter by LLM model
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = ParsingCostAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        rules = ParsedRuleService.get_by_filters(
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        llm_model = query_serializer.validated_data.get('llm_model')
        if llm_model:
            rules = rules.filter(llm_model=llm_model)
        
        total_cost = rules.aggregate(total=Sum('estimated_cost'))['total'] or 0
        total_tokens = rules.aggregate(total=Sum('tokens_used'))['total'] or 0
        count = rules.count()
        avg_cost_per_rule = rules.aggregate(avg=Avg('estimated_cost'))['avg'] or 0.0
        avg_tokens_per_rule = rules.aggregate(avg=Avg('tokens_used'))['avg'] or 0.0
        
        # Group by model
        by_model = rules.values('llm_model').annotate(
            count=Count('id'),
            total_cost=Sum('estimated_cost'),
            total_tokens=Sum('tokens_used'),
            avg_cost=Avg('estimated_cost'),
            avg_tokens=Avg('tokens_used')
        ).order_by('-total_cost')
        
        analytics = {
            'total_cost_usd': float(total_cost),
            'total_tokens': total_tokens,
            'total_rules_parsed': count,
            'average_cost_per_rule': round(float(avg_cost_per_rule), 6),
            'average_tokens_per_rule': round(avg_tokens_per_rule, 2),
            'by_model': [
                {
                    'model': item['llm_model'] or 'unknown',
                    'count': item['count'],
                    'total_cost_usd': float(item['total_cost'] or 0),
                    'total_tokens': item['total_tokens'] or 0,
                    'avg_cost': round(float(item['avg_cost'] or 0), 6),
                    'avg_tokens': round(item['avg_tokens'] or 0, 2),
                }
                for item in by_model
            ],
        }
        
        return self.api_response(
            message="Cost analytics retrieved successfully.",
            data=analytics,
            status_code=status.HTTP_200_OK
        )
