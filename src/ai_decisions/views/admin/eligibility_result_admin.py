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
from ai_decisions.serializers.eligibility_result.admin import EligibilityResultAdminListQuerySerializer
from main_system.utils import paginate_queryset

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
        # Validate query parameters
        query_serializer = EligibilityResultAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        results = EligibilityResultService.get_by_filters(
            case_id=str(validated_params.get('case_id')) if validated_params.get('case_id') else None,
            visa_type_id=str(validated_params.get('visa_type_id')) if validated_params.get('visa_type_id') else None,
            outcome=validated_params.get('outcome'),
            min_confidence=validated_params.get('min_confidence'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_results, pagination_metadata = paginate_queryset(results, page=page, page_size=page_size)
        
        return self.api_response(
            message="Eligibility results retrieved successfully.",
            data={
                'items': EligibilityResultListSerializer(paginated_results, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class EligibilityResultAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed eligibility result with full information.
    
    Endpoint: GET /api/v1/ai-decisions/admin/eligibility-results/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
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


class EligibilityResultAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete eligibility result (for data cleanup/maintenance).
    
    Endpoint: DELETE /api/v1/ai-decisions/admin/eligibility-results/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = EligibilityResultService.delete_eligibility_result(id)
        if not deleted:
            return self.api_response(
                message=f"Eligibility result with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Eligibility result deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )
