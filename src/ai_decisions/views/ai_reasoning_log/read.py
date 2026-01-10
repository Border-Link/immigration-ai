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
from ai_decisions.serializers.ai_reasoning_log.read import AIReasoningLogSerializer, AIReasoningLogListSerializer

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
        case_id = request.query_params.get('case_id', None)
        model_name = request.query_params.get('model_name', None)
        
        try:
            if case_id:
                logs = AIReasoningLogService.get_by_case(case_id)
            elif model_name:
                logs = AIReasoningLogService.get_by_model(model_name)
            else:
                logs = AIReasoningLogService.get_all()
            
            return self.api_response(
                message="AI reasoning logs retrieved successfully.",
                data=AIReasoningLogListSerializer(logs, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving AI reasoning logs: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving AI reasoning logs.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIReasoningLogDetailAPI(AuthAPI):
    """
    Get AI reasoning log by ID.
    
    Endpoint: GET /api/v1/ai-decisions/ai-reasoning-logs/<id>/
    Auth: Required (reviewer only - reviewers review AI decisions)
    """
    permission_classes = [IsReviewer]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving AI reasoning log {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving AI reasoning log.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
