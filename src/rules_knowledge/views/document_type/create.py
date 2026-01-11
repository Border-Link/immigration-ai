from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.serializers.document_type.create import DocumentTypeCreateSerializer
from rules_knowledge.serializers.document_type.read import DocumentTypeSerializer


class DocumentTypeCreateAPI(AuthAPI):
    """Create a new document type. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = DocumentTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_type = DocumentTypeService.create_document_type(
            code=serializer.validated_data.get('code'),
            name=serializer.validated_data.get('name'),
            description=serializer.validated_data.get('description'),
            is_active=serializer.validated_data.get('is_active', True)
        )

        if not document_type:
            return self.api_response(
                message="Document type already exists or error creating document type.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Document type created successfully.",
            data=DocumentTypeSerializer(document_type).data,
            status_code=status.HTTP_201_CREATED
        )

