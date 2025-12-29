from rest_framework import status
from main_system.base.auth_api import AuthAPI
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.serializers.case_document.read import (
    CaseDocumentSerializer,
    CaseDocumentListSerializer
)


class CaseDocumentListAPI(AuthAPI):
    """Get all case documents."""

    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        status_filter = request.query_params.get('status', None)
        
        if case_id:
            case_documents = CaseDocumentService.get_by_case(case_id)
        elif status_filter:
            case_documents = CaseDocumentService.get_by_status(status_filter)
        else:
            case_documents = CaseDocumentService.get_all()

        return self.api_response(
            message="Case documents retrieved successfully.",
            data=CaseDocumentListSerializer(case_documents, many=True).data,
            status_code=status.HTTP_200_OK
        )


class CaseDocumentDetailAPI(AuthAPI):
    """Get case document by ID."""

    def get(self, request, id):
        case_document = CaseDocumentService.get_by_id(id)
        
        if not case_document:
            return self.api_response(
                message=f"Case document with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Case document retrieved successfully.",
            data=CaseDocumentSerializer(case_document).data,
            status_code=status.HTTP_200_OK
        )


class CaseDocumentVerifiedAPI(AuthAPI):
    """Get verified documents for a case."""

    def get(self, request, case_id):
        case_documents = CaseDocumentService.get_verified_by_case(case_id)

        return self.api_response(
            message="Verified case documents retrieved successfully.",
            data=CaseDocumentListSerializer(case_documents, many=True).data,
            status_code=status.HTTP_200_OK
        )

