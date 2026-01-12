"""
Admin API Views for Call Session Management

Admin-only endpoints for managing call sessions.
Access restricted to staff/superusers using AdminPermission.
"""
import logging
from rest_framework import status, serializers
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.base import BaseAdminDetailAPI
from ai_calls.selectors.call_session_selector import CallSessionSelector
from ai_calls.serializers.call_session.read import CallSessionSerializer
from main_system.utils import paginate_queryset

logger = logging.getLogger('django')


class CallSessionAdminListQuerySerializer(serializers.Serializer):
    """Serializer for admin list query parameters."""
    case_id = serializers.UUIDField(required=False, allow_null=True)
    user_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['created', 'ready', 'in_progress', 'completed', 'expired', 'terminated', 'failed'],
        required=False,
        allow_null=True
    )
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)


class CallSessionAdminListAPI(AuthAPI):
    """
    Admin: Get list of all call sessions with advanced filtering.
    
    Endpoint: GET /api/v1/ai-calls/admin/sessions/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - user_id: Filter by user ID
        - status: Filter by status
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CallSessionAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Get all call sessions (admin can see all)
        queryset = CallSessionSelector.get_all(include_deleted=False)
        
        # Apply filters
        if validated_params.get('case_id'):
            queryset = queryset.filter(case_id=validated_params['case_id'])
        
        if validated_params.get('user_id'):
            queryset = queryset.filter(user_id=validated_params['user_id'])
        
        if validated_params.get('status'):
            queryset = queryset.filter(status=validated_params['status'])
        
        if validated_params.get('date_from'):
            queryset = queryset.filter(created_at__gte=validated_params['date_from'])
        
        if validated_params.get('date_to'):
            queryset = queryset.filter(created_at__lte=validated_params['date_to'])
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_sessions, pagination_metadata = paginate_queryset(queryset, page=page, page_size=page_size)
        
        return self.api_response(
            message="Call sessions retrieved successfully.",
            data={
                'items': CallSessionSerializer(paginated_sessions, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class CallSessionAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed call session information.
    
    Endpoint: GET /api/v1/ai-calls/admin/sessions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Call Session"
    
    def get_entity_by_id(self, entity_id):
        """Get call session by ID."""
        return CallSessionSelector.get_by_id(str(entity_id), include_deleted=True)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return CallSessionSerializer
