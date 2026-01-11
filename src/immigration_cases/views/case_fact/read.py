from rest_framework import status
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.serializers.case_fact.read import CaseFactSerializer, CaseFactListSerializer
from immigration_cases.helpers.pagination import paginate_queryset


class CaseFactListAPI(AuthAPI):
    """Get list of case facts. Supports filtering by case_id and pagination."""

    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        
        # Pagination parameters
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        if case_id:
            facts = CaseFactService.get_by_case(case_id)
        else:
            facts = CaseFactService.get_all()

        # Paginate results
        paginated_facts, pagination_metadata = paginate_queryset(facts, page=page, page_size=page_size)

        return self.api_response(
            message="Case facts retrieved successfully.",
            data={
                'items': CaseFactListSerializer(paginated_facts, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class CaseFactDetailAPI(AuthAPI):
    """Get case fact by ID."""

    def get(self, request, id):
        fact = CaseFactService.get_by_id(id)
        if not fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case fact retrieved successfully.",
            data=CaseFactSerializer(fact).data,
            status_code=status.HTTP_200_OK
        )

