from rest_framework import status
from main_system.base.auth_api import AuthAPI
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.serializers.case_document.create import CaseDocumentCreateSerializer
from document_handling.serializers.case_document.read import CaseDocumentSerializer


class CaseDocumentCreateAPI(AuthAPI):
    """Create a new case document."""

    def post(self, request):
        serializer = CaseDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Note: In a real implementation, file upload would be handled here
        # For now, we assume file_path is provided or will be set by file storage service
        case_document = CaseDocumentService.create_case_document(
            case_id=str(serializer.validated_data.get('case_id')),
            document_type_id=str(serializer.validated_data.get('document_type_id')),
            file_path='',  # Will be set by file storage service
            file_name=serializer.validated_data.get('file_name'),
            file_size=serializer.validated_data.get('file_size'),
            mime_type=serializer.validated_data.get('mime_type'),
            status='uploaded'
        )

        if not case_document:
            return self.api_response(
                message="Error creating case document.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="Case document created successfully.",
            data=CaseDocumentSerializer(case_document).data,
            status_code=status.HTTP_201_CREATED
        )

