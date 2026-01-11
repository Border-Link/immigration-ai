"""
Admin API Views for Immigration Cases Analytics and Statistics

Admin-only endpoints for case analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from immigration_cases.services.case_service import CaseService
from immigration_cases.services.case_fact_service import CaseFactService
from django.db.models import Count, Avg, Sum
from django.utils.dateparse import parse_datetime

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
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            parsed_date_from = parse_datetime(date_from) if date_from else None
            parsed_date_to = parse_datetime(date_to) if date_to else None
            
            # Case statistics
            all_cases = CaseService.get_by_filters(
                date_from=parsed_date_from,
                date_to=parsed_date_to
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
                date_from=parsed_date_from,
                date_to=parsed_date_to
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
        except Exception as e:
            logger.error(f"Error retrieving immigration cases statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving immigration cases statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
