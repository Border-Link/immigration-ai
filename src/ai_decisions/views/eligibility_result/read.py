from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_reasoning_permission import AIReasoningPermission
from ai_decisions.permissions.eligibility_result_permissions import CanViewEligibilityResult
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.serializers.eligibility_result.read import (
    EligibilityResultListQuerySerializer,
    EligibilityResultSerializer,
    EligibilityResultListSerializer
)
from main_system.utils import paginate_queryset


class EligibilityResultListAPI(AuthAPI):
    """
    Get list of eligibility results. Supports filtering by case_id.
    
    Security: Users can only see results for cases they own (unless admin/reviewer).
    """
    permission_classes = [AIReasoningPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = EligibilityResultListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        case_id = validated_params.get('case_id')
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)

        if case_id:
            # Use service method to get results with access check
            results, error = EligibilityResultService.get_by_case_with_access_check(
                str(case_id), 
                request.user
            )
            
            if error:
                status_code = status.HTTP_404_NOT_FOUND if "not found" in error.lower() else status.HTTP_403_FORBIDDEN
                return self.api_response(
                    message=error,
                    data=None,
                    status_code=status_code
                )
        else:
            # Use service method to filter by user access
            results = EligibilityResultService.get_by_user_access(request.user)

        # Paginate results
        paginated_results, pagination_metadata = paginate_queryset(results, page=page, page_size=page_size)

        return self.api_response(
            message="Eligibility results retrieved successfully.",
            data={
                'items': EligibilityResultListSerializer(paginated_results, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class EligibilityResultDetailAPI(AuthAPI):
    """
    Get eligibility result by ID.
    
    Security: Users can only access results for cases they own (unless admin/reviewer).
    """
    permission_classes = [AIReasoningPermission, CanViewEligibilityResult]

    def get(self, request, id):
        result = EligibilityResultService.get_by_id(id)
        if not result:
            return self.api_response(
                message=f"Eligibility result with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Enforce object-level access (case ownership/admin).
        self.check_object_permissions(request, result)

        return self.api_response(
            message="Eligibility result retrieved successfully.",
            data=EligibilityResultSerializer(result).data,
            status_code=status.HTTP_200_OK
        )

