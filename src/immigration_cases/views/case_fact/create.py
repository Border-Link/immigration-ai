from rest_framework import status
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.serializers.case_fact.create import CaseFactCreateSerializer
from immigration_cases.serializers.case_fact.read import CaseFactSerializer


class CaseFactCreateAPI(AuthAPI):
    """Create a new case fact. Authenticated users can create facts."""

    def post(self, request):
        serializer = CaseFactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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

