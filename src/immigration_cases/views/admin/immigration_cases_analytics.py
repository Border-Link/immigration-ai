"""
Admin API Views for Immigration Cases Analytics and Statistics

Admin-only endpoints for case analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from immigration_cases.services.case_service import CaseService
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.serializers.case.admin import CaseAdminStatisticsQuerySerializer
from django.db.models import Count, Avg, Sum

logger = logging.getLogger('django')


class ImmigrationCasesStatisticsAPI(AuthAPI):
    """
    Admin: Get immigration cases statistics and analytics.
    
    Endpoint: GET /api/v1/immigration-cases/admin/statistics/
    Auth: Required (staff/superuser only)
    Query Params:
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CaseAdminStatisticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        date_from = validated_params.get('date_from')
        date_to = validated_params.get('date_to')
        
        # Case statistics
        all_cases = CaseService.get_by_filters(
            date_from=date_from,
            date_to=date_to
        )
        case_stats = {
            'total_cases': all_cases.count(),
            'draft_cases': all_cases.filter(status='draft').count(),
            'evaluated_cases': all_cases.filter(status='evaluated').count(),
            'awaiting_review_cases': all_cases.filter(status='awaiting_review').count(),
            'reviewed_cases': all_cases.filter(status='reviewed').count(),
            'closed_cases': all_cases.filter(status='closed').count(),
            'cases_by_status': dict(all_cases.values('status').annotate(count=Count('id')).order_by('status').values_list('status', 'count')),
            'cases_by_jurisdiction': dict(all_cases.values('jurisdiction').annotate(count=Count('id')).order_by('jurisdiction').values_list('jurisdiction', 'count')),
            'cases_by_user': dict(all_cases.values('user__email').annotate(count=Count('id')).order_by('user__email').values_list('user__email', 'count')),
        }
        
        # Case Fact statistics
        all_facts = CaseFactService.get_by_filters(
            date_from=date_from,
            date_to=date_to
        )
        fact_stats = {
            'total_facts': all_facts.count(),
            'facts_by_source': dict(all_facts.values('source').annotate(count=Count('id')).order_by('source').values_list('source', 'count')),
            'facts_by_key': dict(all_facts.values('fact_key').annotate(count=Count('id')).order_by('fact_key').values_list('fact_key', 'count')),
        }
        
        statistics = {
            'cases': case_stats,
            'case_facts': fact_stats,
        }
        
        return self.api_response(
            message="Immigration cases statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )
