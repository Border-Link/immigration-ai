from rest_framework import status
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.create import CaseCreateSerializer
from immigration_cases.serializers.case.read import CaseSerializer


class CaseCreateAPI(AuthAPI):
    """Create a new case. Authenticated users can create cases."""

    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = CaseService.create_case(
            user_id=serializer.validated_data.get('user_id'),
            jurisdiction=serializer.validated_data.get('jurisdiction'),
            status=serializer.validated_data.get('status', 'draft')
        )

        if not case:
            return self.api_response(
                message="Failed to create case. Please check your input and try again.",
                data={'errors': {'general': 'Case creation failed. Please verify user_id and jurisdiction are valid.'}},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Case created successfully.",
            data=CaseSerializer(case).data,
            status_code=status.HTTP_201_CREATED
        )

