"""
Admin API Views for VisaDocumentRequirement Management

Admin-only endpoints for managing visa document requirements.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.serializers.visa_document_requirement.read import (
    VisaDocumentRequirementSerializer,
    VisaDocumentRequirementListSerializer
)
from rules_knowledge.serializers.visa_document_requirement.admin import (
    VisaDocumentRequirementAdminListQuerySerializer,
    VisaDocumentRequirementUpdateSerializer,
    BulkVisaDocumentRequirementOperationSerializer,
)


class VisaDocumentRequirementAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa document requirements with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-document-requirements/
    Auth: Required (staff/superuser only)
    Query Params:
        - rule_version_id: Filter by rule version
        - document_type_id: Filter by document type
        - mandatory: Filter by mandatory status
        - visa_type_id: Filter by visa type
        - jurisdiction: Filter by jurisdiction
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = VisaDocumentRequirementAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        document_requirements = VisaDocumentRequirementService.get_by_filters(
            rule_version_id=str(validated_params.get('rule_version_id')) if validated_params.get('rule_version_id') else None,
            document_type_id=str(validated_params.get('document_type_id')) if validated_params.get('document_type_id') else None,
            mandatory=validated_params.get('mandatory'),
            visa_type_id=str(validated_params.get('visa_type_id')) if validated_params.get('visa_type_id') else None,
            jurisdiction=validated_params.get('jurisdiction'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        from main_system.utils import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(document_requirements, page=page, page_size=page_size)
        
        return self.api_response(
            message="Visa document requirements retrieved successfully.",
            data={
                'items': VisaDocumentRequirementListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaDocumentRequirementAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed visa document requirement information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-document-requirements/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa document requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa document requirement by ID."""
        return VisaDocumentRequirementService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return VisaDocumentRequirementSerializer


class VisaDocumentRequirementAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update visa document requirement.
    
    Endpoint: PATCH /api/v1/rules-knowledge/admin/visa-document-requirements/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa document requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa document requirement by ID."""
        return VisaDocumentRequirementService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return VisaDocumentRequirementUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return VisaDocumentRequirementSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the visa document requirement."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return VisaDocumentRequirementService.update_document_requirement(str(entity.id), **update_fields)


class VisaDocumentRequirementAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete visa document requirement.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-document-requirements/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa document requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa document requirement by ID."""
        return VisaDocumentRequirementService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the visa document requirement."""
        return VisaDocumentRequirementService.delete_document_requirement(str(entity.id))


class BulkVisaDocumentRequirementOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on visa document requirements.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-document-requirements/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk visa document requirement operation serializer."""
        return BulkVisaDocumentRequirementOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Visa document requirement"
    
    def get_entity_by_id(self, entity_id):
        """Get visa document requirement by ID."""
        return VisaDocumentRequirementService.get_by_id(entity_id)
    
    def get_entity_ids(self, validated_data):
        """Override to use document_requirement_ids field name."""
        return validated_data.get('document_requirement_ids', [])
    
    def get_entity_id_field_name(self):
        """Override to use document_requirement_id field name."""
        return 'document_requirement_id'
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the visa document requirement."""
        if operation == 'set_mandatory':
            return VisaDocumentRequirementService.update_document_requirement(str(entity.id), mandatory=True)
        elif operation == 'set_optional':
            return VisaDocumentRequirementService.update_document_requirement(str(entity.id), mandatory=False)
        elif operation == 'delete':
            return VisaDocumentRequirementService.delete_document_requirement(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
