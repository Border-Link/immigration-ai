"""
Admin API Views for EligibilityResult Management

Admin-only endpoints for managing eligibility results.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.serializers.eligibility_result.read import EligibilityResultSerializer, EligibilityResultListSerializer

logger = logging.getLogger('django')


class EligibilityResultAdminListAPI(AuthAPI):
    """
    Admin: Get list of all eligibility results with advanced filtering.
    
    Endpoint: GET /api/v1/ai-decisions/admin/eligibility-results/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - visa_type_id: Filter by visa type ID
        - outcome: Filter by outcome
        - min_confidence: Filter by minimum confidence
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        visa_type_id = request.query_params.get('visa_type_id', None)
        outcome = request.query_params.get('outcome', None)
        min_confidence = request.query_params.get('min_confidence', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            from django.utils.dateparse import parse_datetime
            
            # Parse parameters
            min_confidence_float = float(min_confidence) if min_confidence else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            results = EligibilityResultService.get_by_filters(
                case_id=case_id,
                visa_type_id=visa_type_id,
                outcome=outcome,
                min_confidence=min_confidence_float,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Eligibility results retrieved successfully.",
                data=EligibilityResultListSerializer(results, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving eligibility results: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving eligibility results.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EligibilityResultAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed eligibility result with full information.
    
    Endpoint: GET /api/v1/ai-decisions/admin/eligibility-results/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            result = EligibilityResultService.get_by_id(id)
            if not result:
                return self.api_response(
                    message=f"Eligibility result with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Eligibility result retrieved successfully.",
                data=EligibilityResultSerializer(result).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving eligibility result {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving eligibility result.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EligibilityResultAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete eligibility result (for data cleanup/maintenance).
    
    Endpoint: DELETE /api/v1/ai-decisions/admin/eligibility-results/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            result = EligibilityResultService.get_by_id(id)
            if not result:
                return self.api_response(
                    message=f"Eligibility result with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = EligibilityResultService.delete_eligibility_result(id)
            if deleted:
                return self.api_response(
                    message="Eligibility result deleted successfully.",
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error deleting eligibility result.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error deleting eligibility result {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting eligibility result.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
