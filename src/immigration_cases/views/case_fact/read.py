from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.case_fact_permission import CaseFactPermission
from main_system.permissions.role_checker import RoleChecker
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case_fact.read import (
    CaseFactListQuerySerializer,
    CaseFactSerializer,
    CaseFactListSerializer
)
from main_system.utils import paginate_queryset


class CaseFactListAPI(AuthAPI):
    """Get list of case facts. Supports filtering by case_id and pagination."""
    permission_classes = [CaseFactPermission]

    def get(self, request):
        # Validate query parameters
        query_serializer = CaseFactListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        case_id = validated_params.get('case_id')
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)

        # Security: Non-staff users must scope facts to a case they can access.
        if not RoleChecker.is_staff(request.user):
            if not case_id:
                return self.api_response(
                    message="case_id is required.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            case = CaseService.get_by_id(str(case_id))
            if not case:
                return self.api_response(
                    message=f"Case with ID '{case_id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            # Reuse CaseFactPermission's underlying ownership logic via CaseFactPermission on a fact object
            # isn't possible here; instead enforce case ownership/staff access.
            if str(case.user.id) != str(request.user.id):
                return self.api_response(
                    message="You do not have permission to access facts for this case.",
                    data=None,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            facts = CaseFactService.get_by_case(str(case_id))
        else:
            facts = CaseFactService.get_by_case(str(case_id)) if case_id else CaseFactService.get_all()

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
    permission_classes = [CaseFactPermission]

    def get(self, request, id):
        fact = CaseFactService.get_by_id(id)
        if not fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, fact)

        return self.api_response(
            message="Case fact retrieved successfully.",
            data=CaseFactSerializer(fact).data,
            status_code=status.HTTP_200_OK
        )

