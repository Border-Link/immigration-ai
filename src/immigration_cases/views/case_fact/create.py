from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.case_fact_permission import CaseFactPermission
from main_system.permissions.case_permission import CasePermission
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case_fact.create import CaseFactCreateSerializer
from immigration_cases.serializers.case_fact.read import CaseFactSerializer


class CaseFactCreateAPI(AuthAPI):
    """Create a new case fact. Authenticated users can create facts."""
    permission_classes = [CaseFactPermission]

    def post(self, request):
        serializer = CaseFactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Enforce ownership / access for fact creation (object-level permission requires a case instance).
        case = CaseService.get_by_id(serializer.validated_data.get('case_id'))
        if not case:
            return self.api_response(
                message="Case not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not CasePermission().has_object_permission(request, self, case):
            return self.api_response(
                message="You do not have permission to submit facts for this case.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        fact = CaseFactService.create_case_fact(
            case_id=serializer.validated_data.get('case_id'),
            fact_key=serializer.validated_data.get('fact_key'),
            fact_value=serializer.validated_data.get('fact_value'),
            source=serializer.validated_data.get('source', 'user')
        )

        if not fact:
            return self.api_response(
                message="Failed to create case fact. Please check your input and try again.",
                data={'errors': {'general': 'Case fact creation failed. Please verify case_id, fact_key, and fact_value are valid.'}},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Case fact created successfully.",
            data=CaseFactSerializer(fact).data,
            status_code=status.HTTP_201_CREATED
        )

