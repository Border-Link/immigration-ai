from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.document_permission import DocumentPermission
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.file_storage_service import FileStorageService
from document_handling.serializers.case_document.create import CaseDocumentCreateSerializer
from document_handling.serializers.case_document.read import CaseDocumentSerializer
import logging

logger = logging.getLogger('django')


class CaseDocumentCreateAPI(AuthAPI):
    """Create a new case document with file upload."""
    permission_classes = [DocumentPermission]

    def post(self, request):
        serializer = CaseDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated data
        case_id = str(serializer.validated_data.get('case_id'))
        document_type_id = str(serializer.validated_data.get('document_type_id'))
        file = serializer.validated_data.get('file')
        file_name = serializer.validated_data.get('file_name')
        file_size = serializer.validated_data.get('file_size')
        mime_type = serializer.validated_data.get('mime_type')

        # Store file
        file_path, storage_error = FileStorageService.store_file(
            file=file,
            case_id=case_id,
            document_type_id=document_type_id
        )

        if not file_path:
            logger.error(f"File storage failed: {storage_error}")
            return self.api_response(
                message=f"Error storing file: {storage_error}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create case document record
        case_document = CaseDocumentService.create_case_document(
            case_id=case_id,
            document_type_id=document_type_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            status='uploaded'
        )

        if not case_document:
            # If document creation fails, try to delete the stored file
            FileStorageService.delete_file(file_path)
            return self.api_response(
                message="Error creating case document.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"Case document created successfully: {case_document.id}, file stored at: {file_path}")

        return self.api_response(
            message="Case document created successfully.",
            data=CaseDocumentSerializer(case_document).data,
            status_code=status.HTTP_201_CREATED
        )

