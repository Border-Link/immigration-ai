from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.case_permission import CasePermission
from main_system.permissions.role_checker import RoleChecker
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.create import CaseCreateSerializer
from immigration_cases.serializers.case.read import CaseSerializer


class CaseCreateAPI(AuthAPI):
    """Create a new case. Authenticated users can create cases."""
    permission_classes = [CasePermission]

    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Security: Regular users can only create cases for themselves.
        # Staff/superadmin may create cases on behalf of another user.
        requested_user_id = serializer.validated_data.get('user_id')
        if not RoleChecker.is_staff(request.user) and str(requested_user_id) != str(request.user.id):
            return self.api_response(
                message="You do not have permission to create a case for another user.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        case = CaseService.create_case(
            user_id=serializer.validated_data.get('user_id'),
            jurisdiction=serializer.validated_data.get('jurisdiction'),
            status=serializer.validated_data.get('status', 'draft')
        )

        if not case:
            return self.api_response(
                message="Failed to create case. Completed payment is required before creating a case.",
                data={'errors': {'general': 'Case creation failed. Ensure you have a completed payment, and verify user_id/jurisdiction are valid.'}},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Case created successfully.",
            data=CaseSerializer(case).data,
            status_code=status.HTTP_201_CREATED
        )

