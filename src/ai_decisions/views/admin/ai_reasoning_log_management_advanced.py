"""
Advanced Admin API Views for AIReasoningLog Management

Advanced admin-only endpoints for comprehensive AI reasoning log management.
Includes bulk operations, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.ai_reasoning_log_service import AIReasoningLogService
from ai_decisions.serializers.ai_reasoning_log.admin import BulkAIReasoningLogOperationSerializer

logger = logging.getLogger('django')


class BulkAIReasoningLogOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on AI reasoning logs.
    
    Endpoint: POST /api/v1/ai-decisions/admin/ai-reasoning-logs/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkAIReasoningLogOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        log_ids = serializer.validated_data['log_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for log_id in log_ids:
                try:
                    if operation == 'delete':
                        deleted = AIReasoningLogService.delete_reasoning_log(str(log_id))
                        if deleted:
                            results['success'].append(str(log_id))
                        else:
                            results['failed'].append({
                                'log_id': str(log_id),
                                'error': 'Failed to delete or log not found'
                            })
                except Exception as e:
                    results['failed'].append({
                        'log_id': str(log_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
