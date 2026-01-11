from rest_framework import status
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer, CaseListSerializer
from immigration_cases.helpers.pagination import paginate_queryset


class CaseListAPI(AuthAPI):
    """Get list of cases. Supports filtering by user_id, status, jurisdiction and pagination."""

    def get(self, request):
        user_id = request.query_params.get('user_id', None)
        status_filter = request.query_params.get('status', None)
        jurisdiction = request.query_params.get('jurisdiction', None)
        
        # Pagination parameters
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        if user_id:
            cases = CaseService.get_by_user(user_id)
        else:
            cases = CaseService.get_all()

        # Apply additional filters if needed
        if status_filter:
            cases = cases.filter(status=status_filter)
        if jurisdiction:
            cases = cases.filter(jurisdiction=jurisdiction)

        # Paginate results
        paginated_cases, pagination_metadata = paginate_queryset(cases, page=page, page_size=page_size)

        return self.api_response(
            message="Cases retrieved successfully.",
            data={
                'items': CaseListSerializer(paginated_cases, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class CaseDetailAPI(AuthAPI):
    """Get case by ID."""

    def get(self, request, id):
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case retrieved successfully.",
            data=CaseSerializer(case).data,
            status_code=status.HTTP_200_OK
        )

