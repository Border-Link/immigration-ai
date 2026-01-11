"""
Admin API Views for AIReasoningLog Management

Admin-only endpoints for managing AI reasoning logs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.ai_reasoning_log_service import AIReasoningLogService
from ai_decisions.serializers.ai_reasoning_log.read import AIReasoningLogSerializer, AIReasoningLogListSerializer
from ai_decisions.serializers.ai_reasoning_log.admin import AIReasoningLogAdminListQuerySerializer
from ai_decisions.helpers.pagination import paginate_queryset

logger = logging.getLogger('django')


class AIReasoningLogAdminListAPI(AuthAPI):
    """
    Admin: Get list of all AI reasoning logs with advanced filtering.
    
    Endpoint: GET /api/v1/ai-decisions/admin/ai-reasoning-logs/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - model_name: Filter by model name
        - min_tokens: Filter by minimum tokens used
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = AIReasoningLogAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        logs = AIReasoningLogService.get_by_filters(
            case_id=str(validated_params.get('case_id')) if validated_params.get('case_id') else None,
            model_name=validated_params.get('model_name'),
            min_tokens=validated_params.get('min_tokens'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_logs, pagination_metadata = paginate_queryset(logs, page=page, page_size=page_size)
        
        return self.api_response(
            message="AI reasoning logs retrieved successfully.",
            data={
                'items': AIReasoningLogListSerializer(paginated_logs, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class AIReasoningLogAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed AI reasoning log with full prompt and response.
    
    Endpoint: GET /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        log = AIReasoningLogService.get_by_id(id)
        if not log:
            return self.api_response(
                message=f"AI reasoning log with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="AI reasoning log retrieved successfully.",
            data=AIReasoningLogSerializer(log).data,
            status_code=status.HTTP_200_OK
        )


class AIReasoningLogAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete AI reasoning log (for data cleanup/maintenance).
    
    Endpoint: DELETE /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = AIReasoningLogService.delete_reasoning_log(id)
        if not deleted:
            return self.api_response(
                message=f"AI reasoning log with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="AI reasoning log deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )
