"""
Analytics API Views for AI Call Service

Admin-only endpoints for call session analytics and statistics.
Access restricted to staff/superusers using AdminPermission.
"""
import logging
from rest_framework import status, serializers
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from ai_calls.services.call_analytics_service import CallAnalyticsService

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
        statistics = CallAnalyticsService.get_call_session_statistics(date_from=date_from, date_to=date_to)
        
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
        analytics = CallAnalyticsService.get_guardrail_analytics(
            date_from=date_from,
            date_to=date_to,
            event_type=event_type,
        )
        
        return self.api_response(
            message="Guardrail analytics retrieved successfully.",
            data=analytics,
            status_code=status.HTTP_200_OK
        )
