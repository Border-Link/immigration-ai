from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.document_permission import DocumentPermission
from document_handling.services.document_check_service import DocumentCheckService
from document_handling.serializers.document_check.create import DocumentCheckCreateSerializer
from document_handling.serializers.document_check.read import DocumentCheckSerializer


class DocumentCheckCreateAPI(AuthAPI):
    """Create a new document check."""
    permission_classes = [DocumentPermission]

    def post(self, request):
        serializer = DocumentCheckCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_check = DocumentCheckService.create_document_check(
            case_document_id=str(serializer.validated_data.get('case_document_id')),
            check_type=serializer.validated_data.get('check_type'),
            result=serializer.validated_data.get('result'),
            details=serializer.validated_data.get('details'),
            performed_by=serializer.validated_data.get('performed_by')
        )

        if not document_check:
            return self.api_response(
                message="Error creating document check.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self.api_response(
            message="Document check created successfully.",
            data=DocumentCheckSerializer(document_check).data,
            status_code=status.HTTP_201_CREATED
        )

