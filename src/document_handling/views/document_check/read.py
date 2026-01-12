from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.document_permission import DocumentPermission
from document_handling.services.document_check_service import DocumentCheckService
from document_handling.serializers.document_check.read import (
    DocumentCheckSerializer,
    DocumentCheckListSerializer
)


class DocumentCheckListAPI(AuthAPI):
    """Get all document checks."""
    permission_classes = [DocumentPermission]

    def get(self, request):
        case_document_id = request.query_params.get('case_document_id', None)
        check_type = request.query_params.get('check_type', None)
        result = request.query_params.get('result', None)
        
        if case_document_id:
            document_checks = DocumentCheckService.get_by_case_document(case_document_id)
        elif check_type:
            document_checks = DocumentCheckService.get_by_check_type(check_type)
        elif result:
            document_checks = DocumentCheckService.get_by_result(result)
        else:
            document_checks = DocumentCheckService.get_all()

        return self.api_response(
            message="Document checks retrieved successfully.",
            data=DocumentCheckListSerializer(document_checks, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DocumentCheckDetailAPI(AuthAPI):
    """Get document check by ID."""
    permission_classes = [DocumentPermission]

    def get(self, request, id):
        document_check = DocumentCheckService.get_by_id(id)
        
        if not document_check:
            return self.api_response(
                message=f"Document check with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document check retrieved successfully.",
            data=DocumentCheckSerializer(document_check).data,
            status_code=status.HTTP_200_OK
        )

