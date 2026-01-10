"""
Advanced Admin API Views for EligibilityResult Management

Advanced admin-only endpoints for comprehensive eligibility result management.
Includes bulk operations, updates, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.models.eligibility_result import EligibilityResult
from ai_decisions.serializers.eligibility_result.read import EligibilityResultSerializer
from ai_decisions.serializers.eligibility_result.admin import (
    EligibilityResultAdminUpdateSerializer,
    BulkEligibilityResultOperationSerializer,
)

logger = logging.getLogger('django')


class EligibilityResultAdminUpdateAPI(AuthAPI):
    """
    Admin: Update eligibility result.
    
    Endpoint: PATCH /api/v1/ai-decisions/admin/eligibility-results/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = EligibilityResultAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = EligibilityResultService.get_by_id(id)
            if not result:
                return self.api_response(
                    message=f"Eligibility result with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_result = EligibilityResultService.update_eligibility_result(
                id,
                **serializer.validated_data
            )
            
            if updated_result:
                return self.api_response(
                    message="Eligibility result updated successfully.",
                    data=EligibilityResultSerializer(updated_result).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error updating eligibility result.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error updating eligibility result {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating eligibility result.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkEligibilityResultOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on eligibility results.
    
    Endpoint: POST /api/v1/ai-decisions/admin/eligibility-results/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkEligibilityResultOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result_ids = serializer.validated_data['result_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for result_id in result_ids:
                try:
                    result = EligibilityResultService.get_by_id(str(result_id))
                    if not result:
                        results['failed'].append({
                            'result_id': str(result_id),
                            'error': 'Eligibility result not found'
                        })
                        continue
                    
                    if operation == 'delete':
                        deleted = EligibilityResultService.delete_eligibility_result(str(result_id))
                        if deleted:
                            results['success'].append(str(result_id))
                        else:
                            results['failed'].append({
                                'result_id': str(result_id),
                                'error': 'Failed to delete'
                            })
                    elif operation == 'update_outcome':
                        update_data = {}
                        if 'outcome' in serializer.validated_data:
                            update_data['outcome'] = serializer.validated_data['outcome']
                        if 'confidence' in serializer.validated_data:
                            update_data['confidence'] = serializer.validated_data['confidence']
                        if 'reasoning_summary' in serializer.validated_data:
                            update_data['reasoning_summary'] = serializer.validated_data['reasoning_summary']
                        
                        updated = EligibilityResultService.update_eligibility_result(
                            str(result_id),
                            **update_data
                        )
                        if updated:
                            results['success'].append(str(result_id))
                        else:
                            results['failed'].append({
                                'result_id': str(result_id),
                                'error': 'Failed to update'
                            })
                except Exception as e:
                    results['failed'].append({
                        'result_id': str(result_id),
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
