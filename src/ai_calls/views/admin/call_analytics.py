"""
Analytics API Views for AI Call Service

Admin-only endpoints for call session analytics and statistics.
Access restricted to staff/superusers using AdminPermission.
"""
import logging
from rest_framework import status, serializers
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from ai_calls.selectors.call_session_selector import CallSessionSelector
from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector
from ai_calls.selectors.call_audit_log_selector import CallAuditLogSelector

logger = logging.getLogger('django')


class CallSessionStatisticsQuerySerializer(serializers.Serializer):
    """Serializer for statistics query parameters."""
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)


class CallSessionStatisticsAPI(AuthAPI):
    """
    Admin: Get call session statistics.
    
    Endpoint: GET /api/v1/ai-calls/admin/statistics/
    Auth: Required (staff/superuser only)
    Query Params:
        - date_from: Filter by date (from)
        - date_to: Filter by date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CallSessionStatisticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        date_from = validated_params.get('date_from')
        date_to = validated_params.get('date_to')
        
        # Base queryset
        queryset = CallSessionSelector.get_all(include_deleted=False)
        
        # Apply date filters
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Calculate statistics
        total_sessions = queryset.count()
        sessions_by_status = dict(
            queryset.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
            .values_list('status', 'count')
        )
        
        # Average duration
        completed_sessions = queryset.filter(status='completed', duration_seconds__isnull=False)
        avg_duration = completed_sessions.aggregate(avg=Avg('duration_seconds'))['avg'] or 0.0
        
        # Total duration
        total_duration = completed_sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
        
        # Retry statistics
        retry_sessions = queryset.filter(parent_session__isnull=False)
        retry_count = retry_sessions.count()
        retry_rate = (retry_count / total_sessions * 100) if total_sessions > 0 else 0.0
        
        # Sessions by user
        sessions_by_user = dict(
            queryset.values('user__email')
            .annotate(count=Count('id'))
            .order_by('-count')
            .values_list('user__email', 'count')[:10]  # Top 10 users
        )
        
        # Sessions by case
        sessions_by_case = dict(
            queryset.values('case_id')
            .annotate(count=Count('id'))
            .order_by('-count')
            .values_list('case_id', 'count')[:10]  # Top 10 cases
        )
        # JSON-safe keys (UUID -> str)
        sessions_by_case = {str(k): v for k, v in sessions_by_case.items()}
        
        statistics = {
            'total_sessions': total_sessions,
            'sessions_by_status': sessions_by_status,
            'average_duration_seconds': round(avg_duration, 2),
            'total_duration_seconds': total_duration,
            'retry_count': retry_count,
            'retry_rate_percent': round(retry_rate, 2),
            'sessions_by_user': sessions_by_user,
            'sessions_by_case': sessions_by_case,
        }
        
        return self.api_response(
            message="Call session statistics retrieved successfully.",
            data=statistics,
            status_code=status.HTTP_200_OK
        )


class GuardrailAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for guardrail analytics query parameters."""
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    event_type = serializers.ChoiceField(
        choices=['guardrail_triggered', 'refusal', 'warning', 'escalation'],
        required=False,
        allow_null=True
    )


class GuardrailAnalyticsAPI(AuthAPI):
    """
    Admin: Get guardrail analytics.
    
    Endpoint: GET /api/v1/ai-calls/admin/guardrail-analytics/
    Auth: Required (staff/superuser only)
    Query Params:
        - date_from: Filter by date (from)
        - date_to: Filter by date (to)
        - event_type: Filter by event type
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = GuardrailAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        date_from = validated_params.get('date_from')
        date_to = validated_params.get('date_to')
        event_type = validated_params.get('event_type')
        
        # Get audit logs
        audit_logs = CallAuditLogSelector.get_all()
        
        # Apply filters
        if date_from:
            audit_logs = audit_logs.filter(created_at__gte=date_from)
        if date_to:
            audit_logs = audit_logs.filter(created_at__lte=date_to)
        if event_type:
            audit_logs = audit_logs.filter(event_type=event_type)
        
        # Calculate statistics
        total_events = audit_logs.count()
        events_by_type = dict(
            audit_logs.values('event_type')
            .annotate(count=Count('id'))
            .order_by('event_type')
            .values_list('event_type', 'count')
        )
        
        # Get call sessions with guardrail triggers
        sessions_with_guardrails = CallSessionSelector.get_all(include_deleted=False).filter(
            Q(warnings_count__gt=0) | Q(refusals_count__gt=0) | Q(escalated=True)
        )
        
        if date_from:
            sessions_with_guardrails = sessions_with_guardrails.filter(created_at__gte=date_from)
        if date_to:
            sessions_with_guardrails = sessions_with_guardrails.filter(created_at__lte=date_to)
        
        total_warnings = sessions_with_guardrails.aggregate(total=Sum('warnings_count'))['total'] or 0
        total_refusals = sessions_with_guardrails.aggregate(total=Sum('refusals_count'))['total'] or 0
        escalated_count = sessions_with_guardrails.filter(escalated=True).count()
        
        analytics = {
            'total_guardrail_events': total_events,
            'events_by_type': events_by_type,
            'total_warnings': total_warnings,
            'total_refusals': total_refusals,
            'escalated_sessions': escalated_count,
            'sessions_with_guardrails': sessions_with_guardrails.count(),
        }
        
        return self.api_response(
            message="Guardrail analytics retrieved successfully.",
            data=analytics,
            status_code=status.HTTP_200_OK
        )
