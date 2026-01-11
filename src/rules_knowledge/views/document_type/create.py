import logging
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.serializers.document_type.create import DocumentTypeCreateSerializer
from rules_knowledge.serializers.document_type.read import DocumentTypeSerializer

logger = logging.getLogger('django')


class DocumentTypeCreateAPI(AuthAPI):
    """Create a new document type. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = DocumentTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
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
        except ValidationError as e:
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating document type: {e}", exc_info=True)
            return self.api_response(
                message="An unexpected error occurred while creating document type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

