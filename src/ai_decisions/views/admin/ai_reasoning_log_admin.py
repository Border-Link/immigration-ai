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
        case_id = request.query_params.get('case_id', None)
        model_name = request.query_params.get('model_name', None)
        min_tokens = request.query_params.get('min_tokens', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            from django.utils.dateparse import parse_datetime
            
            # Parse parameters
            min_tokens_int = int(min_tokens) if min_tokens else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            logs = AIReasoningLogService.get_by_filters(
                case_id=case_id,
                model_name=model_name,
                min_tokens=min_tokens_int,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
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


class AIReasoningLogAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed AI reasoning log with full prompt and response.
    
    Endpoint: GET /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
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


class AIReasoningLogAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete AI reasoning log (for data cleanup/maintenance).
    
    Endpoint: DELETE /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            log = AIReasoningLogService.get_by_id(id)
            if not log:
                return self.api_response(
                    message=f"AI reasoning log with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = AIReasoningLogService.delete_reasoning_log(id)
            if deleted:
                return self.api_response(
                    message="AI reasoning log deleted successfully.",
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error deleting AI reasoning log.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error deleting AI reasoning log {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting AI reasoning log.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
