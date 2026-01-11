"""
AI Reasoning Log Read-Only API Views

Read-only endpoints for viewing AI reasoning logs.
Used for debugging, auditing, and observability.
Access restricted to reviewers (who review AI decisions) and staff/superusers.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_reviewer import IsReviewer
from ai_decisions.services.ai_reasoning_log_service import AIReasoningLogService
from ai_decisions.serializers.ai_reasoning_log.read import (
    AIReasoningLogListQuerySerializer,
    AIReasoningLogSerializer,
    AIReasoningLogListSerializer
)
from main_system.utils import paginate_queryset

logger = logging.getLogger('django')


class AIReasoningLogListAPI(AuthAPI):
    """
    Get list of AI reasoning logs.
    
    Endpoint: GET /api/v1/ai-decisions/ai-reasoning-logs/
    Auth: Required (reviewer only - reviewers review AI decisions)
    Query Params:
        - case_id: Filter by case ID
        - model_name: Filter by model name
    """
    permission_classes = [IsReviewer]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = AIReasoningLogListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        case_id = validated_params.get('case_id')
        model_name = validated_params.get('model_name')
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        
        if case_id:
            logs = AIReasoningLogService.get_by_case(str(case_id))
        elif model_name:
            logs = AIReasoningLogService.get_by_model(model_name)
        else:
            logs = AIReasoningLogService.get_all()
        
        # Paginate results
        paginated_logs, pagination_metadata = paginate_queryset(logs, page=page, page_size=page_size)
        
        return self.api_response(
            message="AI reasoning logs retrieved successfully.",
            data={
                'items': AIReasoningLogListSerializer(paginated_logs, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class AIReasoningLogDetailAPI(AuthAPI):
    """
    Get AI reasoning log by ID.
    
    Endpoint: GET /api/v1/ai-decisions/ai-reasoning-logs/<id>/
    Auth: Required (reviewer only - reviewers review AI decisions)
    """
    permission_classes = [IsReviewer]
    
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
