from rest_framework import status
from main_system.base.auth_api import AuthAPI
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.serializers.eligibility_result.read import (
    EligibilityResultListQuerySerializer,
    EligibilityResultSerializer,
    EligibilityResultListSerializer
)
from ai_decisions.helpers.pagination import paginate_queryset


class EligibilityResultListAPI(AuthAPI):
    """Get list of eligibility results. Supports filtering by case_id."""

    def get(self, request):
        # Validate query parameters
        query_serializer = EligibilityResultListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        case_id = validated_params.get('case_id')
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)

        if case_id:
            results = EligibilityResultService.get_by_case(str(case_id))
        else:
            results = EligibilityResultService.get_all()

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
    """Get eligibility result by ID."""

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

