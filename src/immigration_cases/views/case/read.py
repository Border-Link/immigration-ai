from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.case_permission import CasePermission
from main_system.permissions.role_checker import RoleChecker
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import (
    CaseListQuerySerializer,
    CaseSerializer,
    CaseListSerializer
)
from main_system.utils import paginate_queryset


class CaseListAPI(AuthAPI):
    """Get list of cases. Supports filtering by user_id, status, jurisdiction and pagination."""
    permission_classes = [CasePermission]

    def get(self, request):
        # Validate query parameters
        query_serializer = CaseListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        user_id = validated_params.get('user_id')
        status_filter = validated_params.get('status')
        jurisdiction = validated_params.get('jurisdiction')
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)

        # Security: Non-staff users can only list their own cases.
        if not RoleChecker.is_staff(request.user):
            if user_id and str(user_id) != str(request.user.id):
                return self.api_response(
                    message="You do not have permission to list cases for another user.",
                    data=None,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            cases = CaseService.get_by_user(str(request.user.id))
        else:
            cases = CaseService.get_by_user(str(user_id)) if user_id else CaseService.get_all()

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
    permission_classes = [CasePermission]

    def get(self, request, id):
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Enforce object-level permissions (ownership/role-based access).
        self.check_object_permissions(request, case)

        return self.api_response(
            message="Case retrieved successfully.",
            data=CaseSerializer(case).data,
            status_code=status.HTTP_200_OK
        )

