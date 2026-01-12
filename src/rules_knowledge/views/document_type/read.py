from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_permission import RulePermission
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.serializers.document_type.read import DocumentTypeSerializer, DocumentTypeListSerializer
from main_system.utils import paginate_queryset


class DocumentTypeListAPI(AuthAPI):
    """Get list of document types. Supports filtering by is_active."""
    permission_classes = [RulePermission]

    def get(self, request):
        is_active = request.query_params.get('is_active', None)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            if is_active_bool:
                document_types = DocumentTypeService.get_active()
            else:
                document_types = DocumentTypeService.get_all()
        else:
            document_types = DocumentTypeService.get_all()

        # Paginate results
        paginated_items, pagination_metadata = paginate_queryset(document_types, page=page, page_size=page_size)

        return self.api_response(
            message="Document types retrieved successfully.",
            data={
                'items': DocumentTypeListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class DocumentTypeDetailAPI(AuthAPI):
    """Get document type by ID."""
    permission_classes = [RulePermission]

    def get(self, request, id):
        document_type = DocumentTypeService.get_by_id(id)
        if not document_type:
            return self.api_response(
                message=f"Document type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Document type retrieved successfully.",
            data=DocumentTypeSerializer(document_type).data,
            status_code=status.HTTP_200_OK
        )

